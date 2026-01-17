# Установка
## База
```bash
git clone -b dev https://github.com/artwmana/RAGCoach.git
cd RAGCoach

python -m venv .venv && source .venv/bin/activate

pip install --upgrade pip
pip install -e .[dev]
```

## Docker
```bash
docker compose up -d

docker exec -it ragcoach_ollama ollama pull qwen2.5:3b
```
Qdrant — `http://localhost:6333`, Ollama — `http://localhost:11434`.

## Запуск
```bash
docker run -d --name ragcoach_qdrant -p 6333:6333 qdrant/qdrant:v1.7.3

ollama serve
ollama pull qwen2.5:3b

uvicorn ragcoach.api:app --reload
```
then open http://localhost:8000

![2025-12-14 20 42 06](https://github.com/user-attachments/assets/20e783d3-e2ed-4789-bd74-d802a3dde7d6)
# RAGCoach
RAG exam preparation assistant uploads study materials to Qdrant, answers questions, and checks student answers using a locally running LLM program.

## Stack
- FastAPI + Uvicorn — API 
- Qdrant — vector database
- Ollama — LLM (by default `qwen2.5:3b`)
- SentenceTransformers (`intfloat/e5-base`) — embedding
- pdfplumber — Extract text from PDF

## Features
- PDF upload via API/UI, chunking, and indexing in Qdrant
- Search for relevant fragments by question
- Student answer validation (grading) and RAG evaluation
- Works both in containers (docker-compose) and locally in venv

![2025-12-14 20 42 06](https://github.com/user-attachments/assets/20e783d3-e2ed-4789-bd74-d802a3dde7d6)

## Installation

git clone -b dev https://github.com/artwmana/RAGCoach.git
cd RAGCoach

python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev] 

docker compose up -d
docker exec -it ragcoach_ollama ollama pull qwen2.5:3b

Must be opened:
- UI/API: http://localhost:8000
- Qdrant: http://localhost:6333
- Ollama: http://localhost:11434


docker run -d --name ragcoach_qdrant -p 6333:6333 qdrant/qdrant:v1.7.3
ollama serve
ollama pull qwen2.5:3b

uvicorn ragcoach.api:app --reload

then open http://localhost:8000

## Environment variables
The defaults are already set in .env:
- OLLAMA_URL=http://localhost:11434
- OLLAMA_MODEL=qwen2.5:3b
- QDRANT_URL=http://localhost:6333
- EMBEDDING_MODEL=intfloat/e5-base

## API
- POST /api/upload_pdfs — upload a PDF, parse it, and index it
- POST /api/search — search by question
- POST /api/grade — grade a student's answer
- POST /api/evaluate — evaluate a model's answer
- GET / — simple UI page
