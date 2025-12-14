"""Upload lecture chunks from ``pdf_to_json`` output into Qdrant."""
from __future__ import annotations

from pathlib import Path

from .qdrant_service import (
    DEFAULT_COLLECTION,
    DEFAULT_MODEL,
    DEFAULT_QDRANT_API_KEY,
    DEFAULT_QDRANT_URL,
    QdrantService,
)


class LectureJsonUploader:
    """Takes JSON produced by ``pdf_to_json`` and stores embeddings in Qdrant."""

    def __init__(
        self,
        collection: str = DEFAULT_COLLECTION,
        embedding_model: str = DEFAULT_MODEL,
        chunk_words: int = 150,
        qdrant_url: str = DEFAULT_QDRANT_URL,
        qdrant_api_key: str | None = DEFAULT_QDRANT_API_KEY,
    ):
        self.service = QdrantService(
            collection=collection,
            embedding_model=embedding_model,
            chunk_words=chunk_words,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
        )

    def ingest(self, json_path: str | Path, source_name: str | None = None) -> int:
        return self.service.ingest_json(json_path=json_path, source_name=source_name)
