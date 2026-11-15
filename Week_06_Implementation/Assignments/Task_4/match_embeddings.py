"""Match a JSON query embedding against Task 3's stored repository chunks.

Example (from Task_4):
    python -B match_embeddings.py example_query_embedding.json --top-k 5

A query file may contain a JSON array or an object with an "embedding" array.
Output is a JSON array of ranked results, including full source content.
"""

import argparse
import json
from numbers import Integral, Real
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
TASK_3 = HERE.parent / "Task_3"
DEFAULT_STORAGE = TASK_3 / "chunk_embeddings.json"
DIMENSIONS = 384


def reject_constant(value):
    raise ValueError(f"Non-finite JSON value is not allowed: {value}")


def read_json(path):
    """Read UTF-8 JSON, rejecting nonstandard NaN and Infinity constants."""
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream, parse_constant=reject_constant)


def query_vector(value):
    """Validate and normalize a nonzero vector without overflow/underflow."""
    if not isinstance(value, (list, tuple, np.ndarray)):
        raise ValueError("Query embedding must be an array of 384 numbers")
    if isinstance(value, np.ndarray) and value.ndim != 1:
        raise ValueError("Query embedding must be a one-dimensional array")
    if len(value) != DIMENSIONS:
        raise ValueError(f"Query embedding must have {DIMENSIONS} dimensions; got {len(value)}")
    if any(isinstance(number, (bool, np.bool_)) or not isinstance(number, Real)
           for number in value):
        raise ValueError("Query dimensions must be numbers, not booleans, strings or nested arrays")
    try:
        vector = np.asarray(value, dtype=np.float64)
    except (OverflowError, TypeError, ValueError) as error:
        raise ValueError("Query dimensions must be finite floating-point numbers") from error
    if not np.isfinite(vector).all():
        raise ValueError("Query embedding must not contain NaN or Infinity")
    scale = np.max(np.abs(vector))
    if scale == 0:
        raise ValueError("Query embedding must be nonzero for cosine similarity")
    vector = vector / scale
    return vector / np.linalg.norm(vector)


def load_query_embedding(path):
    """Accept a bare vector or an object containing an 'embedding' vector."""
    value = read_json(path)
    if isinstance(value, dict):
        if "embedding" not in value:
            raise ValueError("Query JSON object must contain an 'embedding' field")
        value = value["embedding"]
    # Validate here so bad CLI input fails before importing model libraries.
    query_vector(value)
    return value


def task3_helpers():
    """Reuse Task 3 without editing it or loading any model weights."""
    task3_path = str(TASK_3)
    if task3_path not in sys.path:
        sys.path.insert(0, task3_path)
    from generate_embeddings import validate_dataset
    from search_chunks import rank_chunks
    return validate_dataset, rank_chunks


def validate_storage_structure(dataset):
    """Check result metadata before Task 3 validates the model and vectors."""
    if not isinstance(dataset, dict) or not isinstance(dataset.get("model"), dict):
        raise ValueError("Storage must be an object with model metadata and chunks")
    chunks = dataset.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("Storage must contain a nonempty chunks array")
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError("Each stored chunk must be an object")
        for key in ("chunk_id", "file_path", "content", "embedding", "start_line", "end_line"):
            if key not in chunk:
                raise ValueError(f"Stored chunk is missing {key!r}")
        if any(not isinstance(chunk[key], str) or not chunk[key]
               for key in ("chunk_id", "file_path")):
            raise ValueError("Stored chunk IDs and file paths must be nonempty strings")
        if not isinstance(chunk["content"], str):
            raise ValueError("Stored chunk content must be text")
        if (type(chunk["start_line"]) is not int or type(chunk["end_line"]) is not int
                or not 1 <= chunk["start_line"] <= chunk["end_line"]):
            raise ValueError("Stored chunk line ranges must be positive inclusive integers")
    if "name" not in dataset["model"] or "dimensions" not in dataset["model"]:
        raise ValueError("Storage model metadata must include name and dimensions")


def match_embeddings(query_embedding, storage=DEFAULT_STORAGE, top_k=5):
    """Return up to top_k chunks ranked by descending cosine similarity.

    query_embedding: a 384-number sequence in Task 3's embedding space.
    storage: a storage JSON path or an already-loaded Task 3 dataset dictionary.
    top_k: positive integer; requests larger than the collection return all chunks.

    Results use Task 3's fields: rank, score, chunk_id, file_path, start_line,
    end_line, and content. Raises ValueError for invalid vectors/storage/top_k.
    File access errors propagate to the caller. No files are written.
    """
    if isinstance(top_k, (bool, np.bool_)) or not isinstance(top_k, Integral) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    vector = query_vector(query_embedding)
    dataset = read_json(storage) if isinstance(storage, (str, Path)) else storage
    validate_storage_structure(dataset)
    validate_dataset, rank_chunks = task3_helpers()
    matrix = validate_dataset(dataset)
    return rank_chunks(dataset["chunks"], matrix, vector, int(top_k))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_embedding", type=Path, help="JSON vector or object containing 'embedding'")
    parser.add_argument("--storage", type=Path, default=DEFAULT_STORAGE)
    parser.add_argument("--top-k", type=int, default=5, help="Number of matches (default: 5)")
    args = parser.parse_args()
    try:
        query = load_query_embedding(args.query_embedding)
        results = match_embeddings(query, args.storage, args.top_k)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
