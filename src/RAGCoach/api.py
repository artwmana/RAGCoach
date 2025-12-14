"""FastAPI entrypoint for ingestion, search, grading, and the UI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ragcoach.infrastructure.db import QdrantService, pdf_to_json
from ragcoach.main import build_grader, build_rag_evaluator


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = Path(__file__).resolve().parent / "application" / "frontend"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
JSON_DIR = BASE_DIR / "data" / "json"

service = QdrantService()
grader = build_grader()
evaluator = build_rag_evaluator()
app = FastAPI(title="RAGCoach API")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


class IngestRequest(BaseModel):
    json_path: str = Field(..., description="Path to pdf_to_json output")
    source_name: Optional[str] = Field(None, description="Optional name for source id")


class SearchRequest(BaseModel):
    question: Optional[str] = Field(None, description="Question text")
    question_path: Optional[str] = Field(
        None, description="Path to file; first non-empty line will be used if question is omitted"
    )
    top_k: int = Field(5, ge=1, le=20, description="How many results to return")


class GradeRequest(BaseModel):
    question: str = Field(..., description="Exam question text")
    student_answer: str = Field(..., description="Learner answer to grade")
    lecture_snippet: Optional[str] = Field(None, description="Optional lecture context")


class PromptRequest(BaseModel):
    prompt: str = Field(..., description="Free-form prompt to send to LLM")


@app.get("/", response_class=HTMLResponse)
def index():
    if not FRONTEND_DIR.exists():
        return HTMLResponse("<h1>RAGCoach API</h1><p>Frontend is not built.</p>", status_code=200)
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>RAGCoach API</h1><p>Frontend missing index.html.</p>", status_code=200)
    return FileResponse(index_path)


@app.post("/ingest")
@app.post("/api/ingest")
def ingest(body: IngestRequest):
    path = Path(body.json_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {body.json_path}")
    inserted = service.ingest_json(json_path=path, source_name=body.source_name)
    return {"inserted": inserted}


@app.post("/search")
@app.post("/api/search")
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


@app.post("/api/upload_pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    source_name: Optional[str] = Form(None),
    chunk_words: int = Form(150),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Загрузите PDF-файл")
    if chunk_words <= 0:
        raise HTTPException(status_code=400, detail="chunk_words должен быть положительным")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    pdf_path = UPLOAD_DIR / file.filename
    pdf_path.write_bytes(await file.read())

    json_path = JSON_DIR / f"{Path(file.filename).stem}.json"
    ok = pdf_to_json(str(pdf_path), str(json_path))
    if not ok:
        raise HTTPException(status_code=500, detail="Не удалось извлечь текст из PDF")

    service.chunk_words = chunk_words or service.chunk_words
    try:
        inserted = service.ingest_json(json_path=json_path, source_name=source_name or Path(file.filename).stem)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "uploaded": file.filename,
        "json_path": str(json_path),
        "inserted": inserted,
        "collection": service.collection,
        "chunk_words": service.chunk_words,
    }


@app.post("/api/grade")
async def grade_answer(body: GradeRequest):
    result = await grader(body.question, body.student_answer, body.lecture_snippet)
    return {"result": result}


@app.post("/api/evaluate")
async def evaluate_prompt(body: PromptRequest):
    result = await evaluator(body.prompt)
    return {"result": result}


if __name__ == "__main__":
    uvicorn.run("ragcoach.api:app", host="0.0.0.0", port=8000, reload=False)
