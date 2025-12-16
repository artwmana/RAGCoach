"""Helpers to chunk text, embed, store, and search in Qdrant."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from ragcoach.embeddings.model import EmbeddingModel


# Align default with EmbeddingModel default (dim=768) to avoid size mismatch by default.
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/e5-base")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "lectures")
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


class QdrantService:
    """One place for chunking, embedding, ingestion, and search."""

    def __init__(
        self,
        collection: str | None = None,
        embedding_model: str = DEFAULT_MODEL,
        chunk_words: int = 150,
        qdrant_url: str | None = DEFAULT_QDRANT_URL,
        qdrant_api_key: str | None = DEFAULT_QDRANT_API_KEY,
    ) -> None:
        self.collection = (collection or DEFAULT_COLLECTION or "lectures").strip()
        if not self.collection:
            raise ValueError("Qdrant collection name is empty. Set QDRANT_COLLECTION or pass collection=...")

        self.chunk_words = chunk_words
        self.embedder = EmbeddingModel(embedding_model)
        self.qdrant_url = self._normalize_url(qdrant_url or "http://localhost:6333")
        self.api_key = qdrant_api_key
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=qdrant_api_key,
            timeout=60,
            prefer_grpc=False,
            check_compatibility=False,
        )

    @staticmethod
    def chunk_text(text: str, max_words: int) -> list[str]:
        words = text.split()
        return [
            " ".join(words[i : i + max_words])
            for i in range(0, len(words), max_words)
            if words[i : i + max_words]
        ]

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Strip known suffixes accidentally added by users (e.g., /healthz, /collections)."""
        clean = url.rstrip("/")
        for suffix in ("/healthz", "/collections"):
            if clean.endswith(suffix):
                clean = clean[: -len(suffix)]
        return clean

    @staticmethod
    def _load_json(path: Path) -> dict[str, str]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON content must be an object mapping page keys to text")
        return data

    @staticmethod
    def load_question_from_file(path: str | Path = "data/questions.txt") -> str:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Questions file not found: {path}")
        for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip():
                return line.strip()
        raise ValueError("No question lines found in questions file")

    def _iter_chunks(self, data: dict[str, str], source: str, max_words: int | None = None) -> Iterator[Tuple[str, dict]]:
        max_words = max_words or self.chunk_words
        for page_key, text in data.items():
            cleaned = (text or "").strip()
            if not cleaned:
                continue
            for idx, chunk in enumerate(self.chunk_text(cleaned, max_words)):
                payload = {
                    "source": source,
                    "page": page_key,
                    "chunk_id": idx,
                    "text": chunk,
                }
                yield chunk, payload

    def _ensure_collection(self, vector_size: int) -> None:
        if not self._collection_exists():
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            return

        info = self.client.get_collection(self.collection)
        vectors_config = info.config.params.vectors

        if isinstance(vectors_config, models.VectorParams):
            existing_size = vectors_config.size
        elif isinstance(vectors_config, dict):
            first_vector = next(iter(vectors_config.values()), None)
            existing_size = first_vector.size if isinstance(first_vector, models.VectorParams) else None
        else:
            existing_size = None

        if existing_size and existing_size != vector_size:
            raise ValueError(
                f"Collection '{self.collection}' has vector size {existing_size}, "
                f"but new vectors have size {vector_size}. "
                "Either change QDRANT_COLLECTION or recreate the collection."
            )

    def ingest_json(self, json_path: str | Path, source_name: str | None = None, chunk_words: int | None = None) -> int:
        path = Path(json_path)
        data = self._load_json(path)
        source = source_name or path.stem

        max_words = chunk_words or self.chunk_words
        prepared = list(self._iter_chunks(data, source, max_words))
        if not prepared:
            return 0

        texts, payloads = zip(*prepared)
        vectors = self.embedder.encode(list(texts))

        self._ensure_collection(vector_size=len(vectors[0]))

        points = []
        for vector, payload in zip(vectors, payloads):
            pid = self._make_numeric_id(payload)
            points.append(models.PointStruct(id=pid, vector=vector, payload=payload))
        self._upsert_points(points)
        return len(points)

    def search(self, question: str, top_k: int = 5) -> List[dict]:
        if not self._collection_exists():
            raise ValueError(f"Collection '{self.collection}' not found. Ingest data first.")

        vector = self.embedder.encode([question])[0]
        collection_vector_size = self._get_collection_vector_size()
        if collection_vector_size and len(vector) != collection_vector_size:
            raise ValueError(
                f"Vector size mismatch: collection expects {collection_vector_size}, "
                f"but embedding model produced {len(vector)}. "
                "Use the same EMBEDDING_MODEL as used for ingestion or recreate the collection."
            )
        try:
            result = self._run_search(vector, top_k)
        except UnexpectedResponse as exc:
            raise RuntimeError(
                f"Qdrant search failed for collection '{self.collection}' "
                f"at '{self.qdrant_url}'. Check QDRANT_URL, API key, and collection name."
            ) from exc

        points = result if isinstance(result, list) else getattr(result, "result", []) or []

        normalized = []
        for point in points:
            if isinstance(point, dict):
                pid = point.get("id")
                score = point.get("score")
                payload = point.get("payload") or {}
            else:
                pid = getattr(point, "id", None)
                score = getattr(point, "score", None)
                payload = getattr(point, "payload", None) or {}
            normalized.append({"id": pid, "score": score, "payload": payload})

        return normalized

    def search_from_file(self, path: str | Path = "data/questions.txt", top_k: int = 5) -> List[dict]:
        question = self.load_question_from_file(path)
        return self.search(question=question, top_k=top_k)

    def _collection_exists(self) -> bool:
        """More lenient check than qdrant_client.collection_exists (avoids 404 exceptions)."""
        try:
            self.client.get_collection(self.collection)
            return True
        except UnexpectedResponse as exc:
            if "404" in str(exc) or "Not Found" in str(exc):
                return False
            raise

    def _run_search(self, vector: list[float], top_k: int):
        """Compatibility wrapper for different qdrant-client versions."""
        kwargs = {
            "collection_name": self.collection,
            "query_vector": vector,
            "limit": top_k,
            "with_payload": True,
        }
        if hasattr(self.client, "search"):
            return self.client.search(**kwargs)
        if hasattr(self.client, "search_points"):
            return self.client.search_points(**kwargs)

        # Fallbacks to HTTP API (different client versions expose different methods)
        http_points = getattr(self.client, "http", None)
        if http_points and hasattr(http_points, "points_api"):
            api = http_points.points_api
            if hasattr(api, "search_points"):
                response = api.search_points(
                    collection_name=self.collection,
                    search_request=models.SearchRequest(vector=vector, limit=top_k, with_payload=True),
                )
                return response.result if hasattr(response, "result") else response
            if hasattr(api, "search"):
                return api.search(
                    collection_name=self.collection,
                    search_request=models.SearchRequest(vector=vector, limit=top_k, with_payload=True),
                )

        # Raw HTTP as last resort
        return self._raw_http_search(vector=vector, top_k=top_k)

    def _raw_http_search(self, vector: list[float], top_k: int):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        url = f"{self.qdrant_url}/collections/{self.collection}/points/search"
        payload = {"vector": vector, "limit": top_k, "with_payload": True}
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Qdrant HTTP search failed {exc.response.status_code}: {exc.response.text}"
            ) from exc
        data = resp.json()
        return data.get("result", [])

    def clear_collection(self) -> None:
        """Drop the collection if it exists; ignore if missing."""
        try:
            self.client.delete_collection(self.collection)
            return
        except UnexpectedResponse as exc:
            # Ignore 404-style errors
            if "404" not in str(exc) and "Not Found" not in str(exc):
                raise

        # HTTP fallback
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        url = f"{self.qdrant_url}/collections/{self.collection}"
        resp = httpx.delete(url, headers=headers, timeout=30)
        if resp.status_code not in (200, 202, 404):
            raise RuntimeError(f"Failed to delete collection: {resp.status_code} {resp.text}")

    def _get_collection_vector_size(self) -> int | None:
        try:
            info = self.client.get_collection(self.collection)
        except UnexpectedResponse:
            return None

        vectors_config = info.config.params.vectors
        if isinstance(vectors_config, models.VectorParams):
            return vectors_config.size
        if isinstance(vectors_config, dict):
            first_vector = next(iter(vectors_config.values()), None)
            return first_vector.size if isinstance(first_vector, models.VectorParams) else None
        return None

    @staticmethod
    def _make_numeric_id(payload: dict) -> int:
        """Qdrant 1.7 does not accept arbitrary strings; use a stable numeric id."""
        key = f"{payload.get('source','')}-{payload.get('page','')}-{payload.get('chunk_id','')}"
        return abs(hash(key)) % (2**63)

    def _upsert_points(self, points: list[models.PointStruct]) -> None:
        try:
            self.client.upsert(collection_name=self.collection, points=points, wait=True)
            return
        except UnexpectedResponse:
            pass  # fall back to HTTP

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        url = f"{self.qdrant_url}/collections/{self.collection}/points?wait=true"
        body = {
            "points": [
                {
                    "id": p.id,
                    "vector": p.vector,
                    "payload": p.payload,
                }
                for p in points
            ]
        }
        resp = httpx.put(url, headers=headers, json=body, timeout=60)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Qdrant HTTP upsert failed {exc.response.status_code}: {exc.response.text}"
            ) from exc
