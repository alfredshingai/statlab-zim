# StatLab Zim Backend — Milestone 1

FastAPI backend foundation for Version 2.

## Features (Milestone 1)

- FastAPI application (`app/main.py`)
- Health-check: `GET /health` and `GET /api/v1/health`
- API docs: `/docs`, `/redoc`, `/openapi.json`
- Configuration via `pydantic-settings` (`app/core/config.py`) with `.env` support
- CORS + process-time header
- Error handling: HTTPException, validation 422, generic 500 (debug-aware)
- Example endpoint: `GET /ping`

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# with env file
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# health check
curl http://localhost:8000/health
# -> {"status":"ok","version":"0.1.0","environment":"development","service":"StatLab Zim API"}

# docs
open http://localhost:8000/docs
```

## Test

```bash
pytest tests -v
```

## Project structure

```
backend/
├── app/
│   ├── main.py          # FastAPI factory, middleware, error handlers
│   ├── core/config.py   # Settings (env vars)
│   └── api/routes/health.py  # GET /health, /ping
├── tests/
│   └── test_health.py
├── requirements.txt
└── .env.example
```
