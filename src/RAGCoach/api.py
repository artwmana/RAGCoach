"""FastAPI entrypoint for ingestion and search against Qdrant."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ragcoach.infrastructure.db import QdrantService


service = QdrantService()
app = FastAPI(title="RAGCoach Qdrant API")


class IngestRequest(BaseModel):
    json_path: str = Field(..., description="Path to pdf_to_json output")
    source_name: Optional[str] = Field(None, description="Optional name for source id")


class SearchRequest(BaseModel):
    question: Optional[str] = Field(None, description="Question text")
    question_path: Optional[str] = Field(
        None, description="Path to file; first non-empty line will be used if question is omitted"
    )
    top_k: int = Field(5, ge=1, le=20, description="How many results to return")


@app.post("/ingest")
def ingest(body: IngestRequest):
    path = Path(body.json_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {body.json_path}")
    inserted = service.ingest_json(json_path=path, source_name=body.source_name)
    return {"inserted": inserted}


@app.post("/search")
def search(body: SearchRequest):
    if not body.question and not body.question_path:
        raise HTTPException(status_code=400, detail="Provide either 'question' or 'question_path'")
    if body.question:
        question = body.question
    else:
        try:
            question = service.load_question_from_file(body.question_path or "data/questions.txt")
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        hits = service.search(question, top_k=body.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"question": question, "results": hits}


if __name__ == "__main__":
    uvicorn.run("ragcoach.api:app", host="0.0.0.0", port=8000, reload=False)
