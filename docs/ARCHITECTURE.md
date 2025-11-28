# Architecture
The project is built according to the principles of **Clean Architecture** with division into 4 layers: Domain, Application, Interface Adapters, Infrastructure.

## 2. Layers
### 2.1 Domain Layer

in future

### 2.2 Application Layer

in future

### 2.3 Interface Adapters Layer

in future (FastAPI)

### 2.4 Infrastructure Layer

- Postgres
- Qdrant
- local LLM

## 3. Main pipeline
### 3.1 Loading lecture

1. User uploads file (.pdf)
2. Getting text 
3. Text cleaning
4. Chunking
5. Embeddings
6. Saving to Qdrant and Postgres
7. Logging + metrics

### 3.2 Training session

1. Random Question
2. Speech answer
3. Editing
4. Retrieval Top-K Chunks
5. Prompt Builder
6. LLM
7. Evaluation
8. Saving to Postgres

## 4. Data storage

| Type | database |
|-----|-----------|
| Lectures | Postgres |
| Chunks | Postgres |
| Embeddings | Qdrant |
| Questions | Postgres |
| Attempts | Postgres |
| Marks | Postgres |
| Metrics | Prometheus |
| Logs | Loki |

## 5. docker-compose

- api
- worker
- postgres
- qdrant
- redis
- prometheus
- grafana
- loki

## 6. Observability

Using:
- Prometheus — metrics
- Grafana — dashboards
- Loki — logs
- OpenTelemetry — трейсинг

Controlled:
- Latency RAG
- LLM errors
- Falls
