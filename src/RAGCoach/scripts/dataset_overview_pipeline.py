"""One-shot helper for the 00_dataset_overview.ipynb flow.

Steps:
1) Convert a PDF lecture to JSON (pdf_to_json).
2) Ingest into Qdrant with chunking/embeddings.
3) Search by question (from CLI or file) and print combined context.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ragcoach.infrastructure.db import QdrantService, pdf_to_json


def run(
    pdf_path: Path,
    json_path: Path,
    question: str | None,
    questions_file: Path,
    top_k: int,
    chunk_words: int,
    collection: str | None,
    embedding_model: str | None,
    qdrant_url: str | None,
    qdrant_api_key: str | None,
) -> None:
    pdf_path = pdf_path.expanduser().resolve()
    json_path = json_path.expanduser().resolve()
    questions_file = questions_file.expanduser().resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[1/3] Converting PDF -> JSON: {pdf_path.name} -> {json_path}")
    pdf_to_json(str(pdf_path), str(json_path))

    service = QdrantService(
        collection=collection,
        embedding_model=embedding_model,
        chunk_words=chunk_words,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
    )

    print(f"[2/3] Ingesting JSON into Qdrant (source={pdf_path.stem})")
    inserted = service.ingest_json(json_path, source_name=pdf_path.stem)
    print(f"      Inserted {inserted} chunks")

    print(f"[3/3] Searching top_k={top_k}")
    query = question or service.load_question_from_file(questions_file)
    hits = service.search(query, top_k=top_k)
    context = "\n\n".join([hit.get("payload", {}).get("text", "") for hit in hits])

    print(f"Question: {query}")
    print("\n--- Context (combined) ---\n")
    print(context)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PDF -> JSON -> Qdrant ingest -> search (dataset overview helper)")
    parser.add_argument("--pdf", default="data/lectures/lecture01.pdf", help="Path to lecture PDF")
    parser.add_argument("--json", default="data/output.json", help="Where to store intermediate JSON")
    parser.add_argument("--question", default=None, help="Question text (optional)")
    parser.add_argument("--questions-file", default="data/questions.txt", help="File with questions (first non-empty line)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to fetch")
    parser.add_argument("--chunk-words", type=int, default=150, help="Words per chunk when splitting text")
    parser.add_argument("--collection", default=None, help="Qdrant collection name")
    parser.add_argument("--embedding-model", default=None, help="Embedding model name")
    parser.add_argument("--qdrant-url", default=None, help="Qdrant URL")
    parser.add_argument("--qdrant-api-key", default=None, help="Qdrant API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        pdf_path=Path(args.pdf),
        json_path=Path(args.json),
        question=args.question,
        questions_file=Path(args.questions_file),
        top_k=args.top_k,
        chunk_words=args.chunk_words,
        collection=args.collection,
        embedding_model=args.embedding_model,
        qdrant_url=args.qdrant_url,
        qdrant_api_key=args.qdrant_api_key,
    )


if __name__ == "__main__":
    main()
