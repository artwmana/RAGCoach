"""Load .txt lectures into Qdrant as embeddings (raw HTTP for compatibility)."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Iterable, List, Tuple

from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "lectures")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def find_lecture_dir() -> Path:
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


def embed(model: SentenceTransformer, texts: Iterable[str]) -> List[list[float]]:
    return model.encode(list(texts), normalize_embeddings=True).tolist()


def http_request(method: str, endpoint: str, payload: dict | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if QDRANT_API_KEY:
        headers["api-key"] = QDRANT_API_KEY
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(endpoint, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode()
        if resp.status >= 300:
            raise RuntimeError(f"Qdrant error {resp.status}: {body}")
        return json.loads(body) if body else {}


def ensure_collection(collection: str, vector_size: int) -> None:
    endpoint = f"{QDRANT_URL}/collections/{collection}"
    payload = {"vectors": {"size": vector_size, "distance": "Cosine"}}
    http_request("PUT", endpoint, payload)


def upsert(collection: str, vectors: List[list[float]], payloads: List[dict]) -> None:
    if not vectors:
        return
    ids = [idx for idx, _ in enumerate(vectors)]
    endpoint = f"{QDRANT_URL}/collections/{collection}/points?wait=true"
    # Use batch format for maximum compatibility with older servers
    body = {"batch": {"ids": ids, "vectors": vectors, "payloads": payloads}}
    http_request("PUT", endpoint, body)


def main() -> None:
    lecture_dir = find_lecture_dir()
    chunks = load_chunks(lecture_dir)
    if not chunks:
        print(f"No .txt files found in {lecture_dir}")
        return

    texts, payloads = zip(*chunks)
    model = SentenceTransformer(DEFAULT_MODEL)
    vectors = embed(model, texts)

    ensure_collection(DEFAULT_COLLECTION, vector_size=len(vectors[0]))
    upsert(DEFAULT_COLLECTION, vectors, list(payloads))
    print(f"Inserted {len(vectors)} chunks into collection '{DEFAULT_COLLECTION}' from {lecture_dir}.")


if __name__ == "__main__":
    main()
