"""Retrieve most relevant lecture chunks from Qdrant for a question."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "lectures")


def init_qdrant() -> QdrantClient:
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=60,
        prefer_grpc=False,
        check_compatibility=False,
    )


def embed(text: str, model: SentenceTransformer) -> list[float]:
    return model.encode([text], normalize_embeddings=True)[0].tolist()


def search(question: str, top_k: int = 5) -> List[dict]:
    model = SentenceTransformer(DEFAULT_MODEL)
    vector = embed(question, model)
    client = init_qdrant()
    result = client.search(
        collection_name=DEFAULT_COLLECTION,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )
    return [
        {
            "id": point.id,
            "score": point.score,
            "payload": point.payload,
        }
        for point in result
    ]


def load_question_from_file(path: str = "data/questions.txt") -> str:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Questions file not found: {path}")
    for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            return line.strip()
    raise ValueError("No question lines found in questions file")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Search relevant lecture chunks for a question")
    parser.add_argument("question", nargs="?", help="Question text. If omitted, uses first line from data/questions.txt")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    question = args.question or load_question_from_file()
    hits = search(question, top_k=args.top_k)
    print(f"Question: {question}\n")
    for idx, hit in enumerate(hits, 1):
        payload = hit.get("payload", {}) or {}
        text = payload.get("text") or ""
        print(f"{idx}. score={hit['score']:.4f}, id={hit['id']}, file={payload.get('filename')} chunk={payload.get('chunk_id')}")
        print(text[:500])
        print("-" * 40)


if __name__ == "__main__":
    main()
