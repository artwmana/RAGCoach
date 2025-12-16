# Architecture
Проект следует идеям **Clean Architecture**: Domain → Application → Interface Adapters → Infrastructure. Домена сейчас минимум; ключевые зависимости изолированы через порты/gateway.

## Слои
- **Application** (`src/ragcoach/application`): use-cases для оценки/LLM (`EvaluateWithRagUseCase`, `GradeAnswerUseCase`), порт `LLMGateway`.
- **Interface Adapters**: FastAPI (`src/ragcoach/api.py`) — эндпоинты UI, ingestion, поиск, оценка, свободный промпт.
- **Infrastructure** (`src/ragcoach/infrastructure`):
  - `llm/ollama_gateway.py` — HTTP-клиент Ollama.
  - `db/qdrant_service.py` — чтение JSON, чанкинг, эмбеддинги, upsert/search в Qdrant.
  - `db/reader_pdf.py` — `pdf_to_json`.
  - `settings.py` — конфиг через env.
- **Embeddings** (`src/ragcoach/embeddings/model.py`): SentenceTransformer wrapper.

## Основной pipeline
1. **Upload PDF**: UI (`/api/upload_pdf`) или CLI `python -m ragcoach.scripts.ingest_lectures`.
2. **Extract & chunk**: `pdf_to_json` → `chunk_text`.
3. **Embeddings**: SentenceTransformer (`intfloat/e5-base` по умолчанию).
4. **Ingest**: upsert чанков в Qdrant (коллекция `lectures` по умолчанию).
5. **Search**: `/api/search` возвращает top-k сниппеты и payload.
6. **Grade**: `/api/grade` формирует промпт и отправляет в Ollama (модель `qwen2.5:3b` по умолчанию).
7. **Free prompt**: `/api/evaluate` для произвольных промптов.

## Сервисы и зависимости
- **Qdrant** (vector store) — порт 6333.
- **Ollama** (LLM runtime) — порт 11434.
- **API** (uvicorn FastAPI) — порт 8000, отдаёт статический фронт из `src/ragcoach/application/frontend`.

## Набор окружения
- `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`
- `EMBEDDING_MODEL`
- `OLLAMA_URL`, `OLLAMA_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`

## Поток данных
PDF → JSON (страницы) → чанки (по словам) → эмбеддинги → Qdrant → поиск → топ-к контекст → LLM → оценка/ответ → возврат UI/API.
