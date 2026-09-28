# Fake News Detection using NLP

Aletheia is an evidence-assisted fake-news verification system designed around the project's existing workflow: NLP analysis, trusted-source retrieval, live web evidence, optional image checking, source credibility and conservative final reasoning.

## Architecture

Verification begins with claim extraction and then executes the independent NLP, ChromaDB retrieval, DuckDuckGo search and optional image analysis branches concurrently with `asyncio.gather`. Evidence is assigned a deterministic stance proxy and domain reputation weight. Ollama/Llama 3.1 is used for structured reasoning when reachable; a deterministic evidence-weighted fallback keeps the service available when it is not.

## Local setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
copy .env.example .env   # Windows PowerShell: Copy-Item .env.example .env
uvicorn backend.app:app --reload
```

Open `http://127.0.0.1:8000/`.

The first classifier/embedding/CLIP invocation may download model weights. Hardware requirements depend on the selected model.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Open `http://127.0.0.1:8000/`.

## API

- `POST /api/v1/verify` — verify an article/claim and optional image URL.
- `GET /api/v1/health` — component status without forcing expensive model loading.
- `GET /api/v1/metrics` — lightweight cache/runtime metrics.
- `POST /api/v1/admin/ingest` — refresh the trusted RSS corpus.

### Example request

```json
{
  "article": "A sufficiently long news claim or article goes here.",
  "image_url": "https://example.com/image.jpg"
}
```

## Production hardening checklist

The included package is deployment-oriented but still requires environment-specific controls before internet exposure: TLS/reverse proxy, authentication/authorization for administrative ingestion, rate limiting, distributed Redis caching for multiple replicas, pinned model revisions, resource limits, secrets management, and centralized monitoring.

The built-in cache is intentionally process-local. The system never treats a missing image match as proof of authenticity and never treats model confidence as objective truth.

## Testing

Run:

```bash
pytest -q
```

The included tests cover validation, health, preprocessing and deterministic scoring. Model/network integration tests should be executed in CI with controlled fixtures rather than depending on live third-party services.
