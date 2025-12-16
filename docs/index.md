# RAGCoach — обзор
RAGCoach помогает загрузить лекции (PDF → JSON → Qdrant), искать по ним и оценивать ответы студентов через локальный LLM (Ollama). Есть веб-UI на `http://localhost:8000` и REST API.

## Быстрый старт (Docker Compose)
```bash
git clone -b dev https://github.com/artwmana/RAGCoach.git
cd RAGCoach
docker compose up -d
docker exec -it ragcoach_ollama ollama pull qwen2.5:3b
```
Открыть: `http://localhost:8000`.

## Основной поток
1. Загрузить PDF через UI или CLI-скрипт — извлекаем текст, режем на чанки, считаем эмбеддинги, кладём в Qdrant.
2. Искать по коллекции (top-k) — получаем релевантные сниппеты.
3. Оценивать ответы студентов — LLM возвращает балл 1–10 и короткое обоснование, можно добавить контекст из поиска.
4. Делать свободные LLM-запросы для экспериментов с промптами.

## CLI и API
- CLI: `python -m ragcoach.scripts.ingest_lectures --pdf-dir data/lectures --json-dir data/json`
- API примеры:
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"question": "Что такое градиентный спуск?", "top_k": 5}'

curl -X POST http://localhost:8000/api/grade \
  -H "Content-Type: application/json" \
  -d '{"question":"Что такое backprop?","student_answer":"Это способ...","lecture_snippet":"Контекст..."}'
```

## Полезные ссылки
- Архитектура: `docs/ARCHITECTURE.md`
- Форматы данных и пэйлоады: `docs/DATA_FORMATS.md`
- Датасеты и заметки: `docs/DATASET.md`
