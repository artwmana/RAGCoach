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
```