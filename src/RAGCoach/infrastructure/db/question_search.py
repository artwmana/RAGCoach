"""Retrieve most relevant lecture chunks from Qdrant for a question."""
from __future__ import annotations

import argparse

from .qdrant_service import QdrantService


def main() -> None:
    parser = argparse.ArgumentParser(description="Search relevant lecture chunks for a question")
    parser.add_argument("question", nargs="?", help="Question text. If omitted, uses first line from data/questions.txt")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--questions_file", default="data/questions.txt", help="Path to questions file")
    args = parser.parse_args()

    service = QdrantService()
    question = args.question or service.load_question_from_file(args.questions_file)
    hits = service.search(question, top_k=args.top_k)
    print(f"Question: {question}\n")
    for idx, hit in enumerate(hits, 1):
        payload = hit.get("payload", {}) or {}
        text = payload.get("text") or ""
        print(
            f"{idx}. score={hit['score']:.4f}, id={hit['id']}, "
            f"source={payload.get('source')} page={payload.get('page')} chunk={payload.get('chunk_id')}"
        )
        print(text[:500])
        print("-" * 40)


if __name__ == "__main__":
    main()
