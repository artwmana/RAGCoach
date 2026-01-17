Project for exam preparation
1. Launch the project
2. Download lectures and questions
3. Get a random question
4. The answer will be verified by LLM

# Installation
1. Clone git
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

## Run
```bash
docker run -d --name ragcoach_qdrant -p 6333:6333 qdrant/qdrant:v1.7.3

ollama serve
ollama pull qwen2.5:3b

uvicorn ragcoach.api:app --reload
```
then open http://localhost:8000

![2025-12-14 20 42 06](https://github.com/user-attachments/assets/20e783d3-e2ed-4789-bd74-d802a3dde7d6)
