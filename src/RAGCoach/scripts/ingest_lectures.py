"""Bulk pipeline: PDFs -> JSON (pdf_to_json) -> Qdrant ingest."""
from __future__ import annotations

import argparse
from pathlib import Path

from ragcoach.infrastructure.db import QdrantService, pdf_to_json


def convert_pdf(pdf_path: Path, json_dir: Path) -> Path:
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / f"{pdf_path.stem}.json"
    pdf_to_json(str(pdf_path), str(json_path))
    return json_path


def ingest_all(
    pdf_dir: Path,
    json_dir: Path,
    chunk_words: int,
    collection: str | None = None,
    embedding_model: str | None = None,
    qdrant_url: str | None = None,
    qdrant_api_key: str | None = None,
) -> None:
    pdf_dir = pdf_dir.expanduser().resolve()
    json_dir = json_dir.expanduser().resolve()
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return

    service = QdrantService(
        collection=collection,
        embedding_model=embedding_model or QdrantService.DEFAULT_MODEL,  # type: ignore[attr-defined]
        chunk_words=chunk_words,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
    )

    total_inserted = 0
    for pdf_path in pdf_files:
        print(f"[+] Converting {pdf_path.name} -> JSON")
        json_path = convert_pdf(pdf_path, json_dir)

        print(f"[+] Ingesting {json_path.name} into Qdrant (source={pdf_path.stem})")
        inserted = service.ingest_json(json_path, source_name=pdf_path.stem)
        total_inserted += inserted
        print(f"    Inserted {inserted} chunks")

    print(f"Done. Total chunks inserted: {total_inserted}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert PDFs to JSON and ingest into Qdrant")
    parser.add_argument("--pdf-dir", default="data/lectures", help="Directory with PDF lectures")
    parser.add_argument("--json-dir", default="data/json", help="Where to store intermediate JSON files")
    parser.add_argument("--chunk-words", type=int, default=150, help="Words per chunk for splitting pages")
    parser.add_argument("--collection", default=None, help="Qdrant collection name (defaults to env/QdrantService default)")
    parser.add_argument("--embedding-model", default=None, help="Embedding model name (defaults to env/QdrantService default)")
    parser.add_argument("--qdrant-url", default=None, help="Qdrant URL (defaults to env/QdrantService default)")
    parser.add_argument("--qdrant-api-key", default=None, help="Qdrant API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingest_all(
        pdf_dir=Path(args.pdf_dir),
        json_dir=Path(args.json_dir),
        chunk_words=args.chunk_words,
        collection=args.collection,
        embedding_model=args.embedding_model,
        qdrant_url=args.qdrant_url,
        qdrant_api_key=args.qdrant_api_key,
    )


if __name__ == "__main__":
    main()
