## Installation
```bash
git clone -b dev https://github.com/artwmana/RAGCoach.git
cd RAGCoach
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e .
# Но лучше не . а .[dev]:
# pip install -e .[dev]
ollama serve
ollama pull qwen2.5:3b

uvicorn ragcoach.api:app --reload
```
then open http://localhost:8000

![2025-12-14 20 42 06](https://github.com/user-attachments/assets/20e783d3-e2ed-4789-bd74-d802a3dde7d6)
