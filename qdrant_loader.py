"""Load .txt lectures into Qdrant as embeddings."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "lectures")


def find_lecture_dir() -> Path:
    """Return lecture directory, preferring data/lectures then data/lections."""
    preferred = Path(os.getenv("LECTURES_DIR", "data/lectures"))
    if preferred.exists():
        return preferred
    fallback = Path("data/lections")
    if fallback.exists():
        return fallback
    raise FileNotFoundError("Lecture directory not found (tried data/lectures and data/lections)")


def chunk_text(text: str, max_words: int = 150) -> List[str]:
    words = text.split()
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words) if words[i : i + max_words]]


def load_chunks(directory: Path) -> List[Tuple[str, dict]]:
    """Load all .txt files and return list of (text, payload)."""
    chunks: List[Tuple[str, dict]] = []
    for path in sorted(directory.glob("*.txt")):
        content = path.read_text(encoding="utf-8", errors="ignore")
        for idx, chunk in enumerate(chunk_text(content)):
            payload = {"filename": path.name, "chunk_id": idx, "text": chunk}
            chunks.append((chunk, payload))
    return chunks


def init_qdrant() -> QdrantClient:
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", 6333))
    return QdrantClient(host=host, port=port)


def ensure_collection(client: QdrantClient, collection: str, vector_size: int) -> None:
    client.recreate_collection(
        collection_name=collection,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )


def embed(model: SentenceTransformer, texts: Iterable[str]) -> List[list[float]]:
    return model.encode(list(texts), normalize_embeddings=True).tolist()


def upsert(client: QdrantClient, collection: str, vectors: List[list[float]], payloads: List[dict]) -> None:
    points = [
        models.PointStruct(
            id=f"{payload['filename']}:{payload['chunk_id']}",
            vector=vector,
            payload=payload,
        )
        for vector, payload in zip(vectors, payloads)
    ]
    if points:
        client.upsert(collection_name=collection, points=points)


def main() -> None:
    lecture_dir = find_lecture_dir()
    chunks = load_chunks(lecture_dir)
    if not chunks:
        print(f"No .txt files found in {lecture_dir}")
        return

    texts, payloads = zip(*chunks)
    model = SentenceTransformer(DEFAULT_MODEL)
    vectors = embed(model, texts)

    client = init_qdrant()
    ensure_collection(client, DEFAULT_COLLECTION, vector_size=len(vectors[0]))
    upsert(client, DEFAULT_COLLECTION, vectors, list(payloads))
    print(f"Inserted {len(vectors)} chunks into collection '{DEFAULT_COLLECTION}' from {lecture_dir}.")


if __name__ == "__main__":
    main()
