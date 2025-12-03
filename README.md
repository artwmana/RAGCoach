## Installation
1) База
   ```bash
   git clone -b dev https://github.com/artwmana/RAGCoach.git
   cd RAGCoach
   python -m venv .venv && source .venv/bin/activate
   pip install --upgrade pip
   pip install -e .
   # Но лучше не . а .[dev]:
   # pip install -e .[dev]
   ```
2) Докер 
   ```bash
   docker compose up -d                 # Ollama и Qdrant (последний пока не используется)
   docker compose logs -f qdrant ollama
   ```
3) Должно работать
   ```bash
   docker exec -it ragcoach_ollama ollama pull qwen2.5:3b
   ```

Чтобы выключить:
```bash
docker compose down
```