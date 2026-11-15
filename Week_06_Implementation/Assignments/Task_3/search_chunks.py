"""Search stored repository embeddings with local MiniLM and cosine similarity."""

import argparse
import json
from pathlib import Path
import time

import numpy as np

from generate_embeddings import HERE, embed_texts, load_model, validate_dataset

DEMO_QUERIES = [
    "Find the code responsible for calculating order prices and discounts.",
    "Where is warehouse inventory and stock reservation handled?",
    "Find the implementation of customer credit limits.",
    "Where are order status transitions defined?",
]


def rank_chunks(chunks, matrix, query_vector, top_k=5):
    """Compute exact cosine similarity; stable sorting resolves score ties."""
    if top_k < 1 or not np.isfinite(query_vector).all():
        raise ValueError("Invalid search arguments")
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vector)
    if (norms <= 0).any():
        raise ValueError("Cosine similarity requires nonzero embeddings")
    scores = np.clip((matrix @ query_vector) / norms, -1, 1)
    order = np.argsort(-scores, kind="stable")[:top_k]
    return [{"rank": rank, "score": float(scores[index]),
             **{key: chunks[index][key] for key in
                ("chunk_id", "file_path", "start_line", "end_line", "content")}}
            for rank, index in enumerate(order, 1)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", help="Natural-language coding question (quoted)")
    parser.add_argument("--input", type=Path, default=HERE / "chunk_embeddings.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--demo", action="store_true", help="Run all four assignment queries")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--summary-only", action="store_true", help="Hide full code in console output")
    parser.add_argument("--save-results", type=Path, help="Save ranked results including complete source content")
    args = parser.parse_args()
    if args.demo and args.question:
        parser.error("Choose a question or --demo")
    if not args.demo and (not args.question or not args.question.strip()):
        parser.error("Provide a nonempty question or --demo")
    if args.top_k < 1:
        parser.error("--top-k must be positive")
    if args.save_results and (args.save_results.resolve().parent != HERE
                              or args.save_results.suffix.lower() != ".json"
                              or args.save_results.resolve() == args.input.resolve()):
        parser.error("Save results to a separate JSON file in Task 3")
    dataset = json.loads(args.input.read_text(encoding="utf-8"))
    matrix = validate_dataset(dataset)
    model = load_model(revision=dataset["model"]["revision"], offline=args.offline)
    if model.max_seq_length != dataset["model"]["max_sequence_tokens"]:
        raise ValueError("Model token limit differs from indexing configuration")
    questions = DEMO_QUERIES if args.demo else [args.question.strip()]
    vectors, _ = embed_texts(model, questions, overlap=dataset["model"]["token_overlap"])
    searches = []
    for question, vector in zip(questions, vectors):
        started = time.perf_counter()
        results = rank_chunks(dataset["chunks"], matrix, vector, args.top_k)
        searches.append({"query": question, "ranking_seconds": time.perf_counter() - started, "results": results})
        print(f"\nQuery: {question}")
        for result in results:
            print(f"{result['rank']}. {result['score']:.6f}  {result['file_path']}:{result['start_line']}-{result['end_line']}")
            if not args.summary_only:
                print(result["content"].replace("\r\n", "\n").replace("\r", "\n"))
    if args.save_results:
        args.save_results.write_text(
            json.dumps({"model": dataset["model"], "searches": searches}, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nSaved full result content to {args.save_results}")


if __name__ == "__main__":
    main()

