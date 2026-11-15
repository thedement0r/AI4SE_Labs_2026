"""Generate local MiniLM embeddings for the existing Task 2 chunks."""

import argparse
import ast
from collections import defaultdict
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import textwrap
import time

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).resolve().parent
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# Pin the revision used by the existing storage; no private config API needed.
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
DIMENSIONS = 384
TOKEN_OVERLAP = 32


def load_model(revision=MODEL_REVISION, offline=False):
    """Use CPU inference and a cache isolated from the original repository."""
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    model = SentenceTransformer(
        MODEL_NAME, device="cpu", cache_folder=str(HERE / ".model_cache"),
        revision=revision, local_files_only=offline, trust_remote_code=False,
        token=False,
    )
    model.eval()
    # Sentence Transformers 6 renamed this API; older releases need the fallback.
    get_dimension = getattr(model, "get_embedding_dimension", None)
    if get_dimension is None:
        get_dimension = model.get_sentence_embedding_dimension
    if get_dimension() != DIMENSIONS:
        raise ValueError("Unexpected model embedding dimension")
    return model


def readable_name(name):
    """Expose identifier words to a natural-language model without inventing text."""
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).replace("_", " ")


def symbols_by_file(chunks):
    """Recover enclosing Python symbols from Task 2 data, without reading the repo."""
    grouped = defaultdict(list)
    for chunk in chunks:
        grouped[chunk["file_path"]].append(chunk)
    result = {}
    for path, parts in grouped.items():
        lines = [None] * max(c["end_line"] for c in parts)
        for chunk in parts:
            source_lines = chunk["content"].splitlines(keepends=True)
            if len(source_lines) != chunk["end_line"] - chunk["start_line"] + 1:
                raise ValueError(f"Inconsistent line range: {path}")
            for offset, line in enumerate(source_lines, chunk["start_line"] - 1):
                if lines[offset] is not None and lines[offset] != line:
                    raise ValueError(f"Conflicting overlapping chunks: {path}")
                lines[offset] = line
        if any(line is None for line in lines):
            raise ValueError(f"Missing source lines: {path}")
        records = []
        try:
            tree = ast.parse("".join(lines)) if path.endswith((".py", ".pyw", ".pyi")) else None
        except (SyntaxError, ValueError, RecursionError):
            tree = None

        def visit(node, parents=()):
            scope = parents
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                scope = parents + (node.name,)
                records.append({
                    "name": ".".join(scope), "start": node.lineno,
                    "end": node.end_lineno, "docstring": ast.get_docstring(node) or "",
                })
            for child in ast.iter_child_nodes(node):
                visit(child, scope)

        if tree:
            visit(tree)
        result[path] = records
    return result


def represent_chunk(chunk, symbols):
    selected = [s for s in symbols if s["start"] <= chunk["end_line"] and s["end"] >= chunk["start_line"]]
    names = [s["name"] for s in selected]
    docs = [f"{s['name']}: {s['docstring']}" for s in selected if s["docstring"]]
    # Fragments may begin inside a class. Full-file AST context restores its name/docs.
    text = (
        f"File: {chunk['file_path']}\n"
        f"Symbols: {'; '.join(readable_name(name) for name in names)}\n"
        f"Documentation:\n{chr(10).join(docs)}\n"
        f"Source code:\n{textwrap.dedent(chunk['content'])}"
    )
    return text, names


def token_windows(ids, capacity, overlap):
    """Cover every token; weight each window by the number of newly covered tokens."""
    if not 0 <= overlap < capacity:
        raise ValueError("Invalid token-window overlap")
    start, covered = 0, 0
    while start < len(ids):
        end = min(start + capacity, len(ids))
        yield ids[start:end], end - covered
        covered = end
        if end == len(ids):
            break
        start = end - overlap


def embed_texts(model, texts, overlap=TOKEN_OVERLAP, batch_size=16):
    """Encode complete text with checked overflow windows and no token loss."""
    tokenizer = model.tokenizer
    capacity = model.max_seq_length - tokenizer.num_special_tokens_to_add(pair=False)
    inputs, owners, weights, statistics = [], [], [], []
    for owner, text in enumerate(texts):
        ids = tokenizer.encode(text, add_special_tokens=False, truncation=False, verbose=False)
        if not ids:
            raise ValueError("Cannot embed empty text")
        windows = list(token_windows(ids, capacity, overlap))
        statistics.append({"token_count": len(ids), "window_count": len(windows), "truncated_tokens": 0})
        # The normal tokenizer interface works across Transformers 4 and 5.
        # Overflow keeps the complete text, even though each individual window
        # is limited to max_seq_length (including the model's special tokens).
        encoded = tokenizer(
            text, add_special_tokens=True, truncation=True,
            max_length=model.max_seq_length, stride=overlap,
            return_overflowing_tokens=True, return_special_tokens_mask=True,
            return_attention_mask=True, return_token_type_ids=True,
            padding=False, verbose=False,
        )
        if len(encoded["input_ids"]) != len(windows):
            raise ValueError("Tokenizer overflow differs from expected token windows")
        for index, (window, weight) in enumerate(windows):
            item = {key: encoded[key][index] for key in tokenizer.model_input_names
                    if key in encoded}
            payload = [token for token, special in zip(
                item["input_ids"], encoded["special_tokens_mask"][index]
            ) if not special]
            if payload != window:
                raise ValueError("Tokenizer changed the expected window token IDs")
            if len(item["input_ids"]) > model.max_seq_length:
                raise ValueError("Token window exceeds the model limit")
            inputs.append(item)
            owners.append(owner)
            weights.append(weight)
    sums = np.zeros((len(texts), DIMENSIONS), dtype=np.float64)
    with torch.inference_mode():
        for start in range(0, len(inputs), batch_size):
            features = tokenizer.pad(inputs[start:start + batch_size], padding=True, return_tensors="pt")
            features = {key: value.to(model.device) for key, value in features.items()}
            vectors = model(features)["sentence_embedding"]
            vectors = torch.nn.functional.normalize(vectors, p=2, dim=1).cpu().numpy()
            for offset, vector in enumerate(vectors, start):
                sums[owners[offset]] += vector * weights[offset]
    norms = np.linalg.norm(sums, axis=1, keepdims=True)
    if not np.isfinite(sums).all() or (norms <= 0).any():
        raise ValueError("Invalid embedding values")
    return (sums / norms).astype(np.float32), statistics


def validate_dataset(dataset, originals=None):
    """Reject missing IDs, malformed vectors, nonfinite values, and changed metadata."""
    chunks = dataset["chunks"]
    ids = [chunk["chunk_id"] for chunk in chunks]
    if not chunks or len(set(ids)) != len(ids):
        raise ValueError("Empty dataset or duplicate chunk IDs")
    if dataset["model"]["name"] != MODEL_NAME or dataset["model"]["dimensions"] != DIMENSIONS:
        raise ValueError("Incompatible embedding model")
    for chunk in chunks:
        values = chunk["embedding"]
        if (not isinstance(values, list) or len(values) != DIMENSIONS
                or any(type(value) not in (int, float) for value in values)):
            raise ValueError("Embedding must contain 384 numeric dimensions")
    matrix = np.asarray([chunk["embedding"] for chunk in chunks], dtype=np.float64)
    if not np.isfinite(matrix).all() or not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-5):
        raise ValueError("Embeddings must be finite and unit length")
    if originals is not None:
        source = {chunk["chunk_id"]: chunk for chunk in originals}
        if set(ids) != set(source) or len(chunks) != len(originals):
            raise ValueError("Chunk IDs/count differ from Task 2")
        for chunk in chunks:
            if any(chunk.get(key) != value for key, value in source[chunk["chunk_id"]].items()):
                raise ValueError("Original chunk content/metadata changed")
    return matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE.parent / "Task_2" / "repository_chunks.json")
    parser.add_argument("--output", type=Path, default=HERE / "chunk_embeddings.json")
    parser.add_argument("--offline", action="store_true", help="Use only previously downloaded model files")
    args = parser.parse_args()
    if args.output.resolve().parent != HERE:
        parser.error("Keep output in the Task 3 directory")
    started = time.perf_counter()
    raw = args.input.read_bytes()
    original = json.loads(raw)
    chunks = original["chunks"]
    if not chunks or len({c["chunk_id"] for c in chunks}) != len(chunks):
        raise ValueError("Input chunks must be nonempty and have unique IDs")
    symbols = symbols_by_file(chunks)
    representations = [represent_chunk(chunk, symbols[chunk["file_path"]]) for chunk in chunks]
    print(f"Loading {MODEL_NAME}; input contains {len(chunks)} chunks.", flush=True)
    model = load_model(offline=args.offline)
    encoding_started = time.perf_counter()
    vectors, statistics = embed_texts(model, [text for text, _ in representations])
    encoding_seconds = time.perf_counter() - encoding_started
    enriched = []
    for chunk, (text, names), vector, stats in zip(chunks, representations, vectors, statistics):
        enriched.append({**chunk, "embedding": vector.tolist(), "embedding_text": text,
                         "embedding_symbols": names, "embedding_metadata": stats})
    dataset = {
        "schema_version": 1, "repository": original.get("repository"),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "source_metadata": {key: value for key, value in original.items() if key != "chunks"},
        "model": {"name": MODEL_NAME, "revision": MODEL_REVISION,
                  "dimensions": DIMENSIONS, "max_sequence_tokens": model.max_seq_length,
                  "payload_tokens": model.max_seq_length - model.tokenizer.num_special_tokens_to_add(False),
                  "token_overlap": TOKEN_OVERLAP, "normalized": True, "device": "cpu",
                  "pooling": "new-token-weighted mean of normalized window embeddings, then L2 normalize"},
        "representation": "file path + humanized qualified symbol names + intersecting/enclosing docstrings + full dedented chunk code",
        "packages": {name: version(name) for name in ("sentence-transformers", "transformers", "torch", "numpy")},
        "summary": {"chunks_embedded": len(enriched), "dimensions": DIMENSIONS,
                    "total_tokens": sum(s["token_count"] for s in statistics),
                    "total_windows": sum(s["window_count"] for s in statistics),
                    "multiwindow_chunks": sum(s["window_count"] > 1 for s in statistics),
                    "largest_representation_tokens": max(s["token_count"] for s in statistics),
                    "truncated_tokens": 0, "encoding_seconds": round(encoding_seconds, 3),
                    "total_seconds_including_model_load": round(time.perf_counter() - started, 3)},
        "chunks": enriched,
    }
    validate_dataset(dataset, chunks)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    saved = json.loads(args.output.read_text(encoding="utf-8"))
    validate_dataset(saved, chunks)
    if saved != dataset:
        raise ValueError("JSON round-trip mismatch")
    print(json.dumps(saved["summary"], indent=2))
    print(f"Validated embeddings written to {args.output}")


if __name__ == "__main__":
    main()

