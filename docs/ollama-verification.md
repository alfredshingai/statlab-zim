# Ollama Local-First Verification — Version 3

**Goal:** Run AI explanations without sending data to external services (privacy-preserving, free, offline).

## Verification (WSL / Linux)

Backend defaults to `AI_PROVIDER=mock` (no network, deterministic). To use local LLM:

### 1. Install Ollama

**Windows (recommended for this WSL env):**
- Download from https://ollama.com/download → Install → `ollama run qwen2.5:7b` (model already cached at `~/.ollama/models` as `qwen2.5:7b`, 4.6GB)
- Or `ollama run llama3.1` for Llama

**WSL/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &  # or `ollama run qwen2.5:7b` will auto-serve
ollama list     # should show qwen2.5:7b
curl http://localhost:11434/api/tags  # -> {"models":[...]}
```

### 2. Configure Backend

`backend/.env`:
```
AI_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b   # or llama3.1, matches ollama list
# For WSL talking to Windows Ollama, use http://$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):11434
```

Or one-off:
```bash
AI_PROVIDER=ollama OLLAMA_MODEL=qwen2.5:7b PYTHONPATH=backend uvicorn app.main:app --port 8000
```

### 3. Verify

```bash
# Upload
curl -F "file=@data/sample.csv" http://localhost:8000/datasets/upload
# Ask — should use Ollama, provenance still verified
curl -X POST http://localhost:8000/ai/ask -H "Content-Type: application/json" \
  -d '{"dataset_id":"<id>","question":"Is satisfaction different between age groups?"}' | jq '.llm_meta'
# Expected: {"provider":"ollama","model":"qwen2.5:7b"}

# Test suite: mock is default, ollama fallback tested
AI_PROVIDER=ollama PYTHONPATH=backend pytest backend/tests/test_ai.py::test_local_first_option -v
# When Ollama not running, fallback is mock (no crash):
AI_PROVIDER=ollama PYTHONPATH=backend python -c "
from fastapi.testclient import TestClient
from app.main import app
from app.store.memory import clear_all; import io
clear_all(); c=TestClient(app)
r=c.post('/datasets/upload', files={'file': ('t.csv', io.BytesIO(b'x,y\n1,2\n2,4'), 'text/csv')})
ds=r.json()['dataset_id']
print(c.post('/ai/ask', json={'dataset_id': ds, 'question': 'What is correlation?'}).json()['llm_meta'])
"
# -> {'provider': 'mock', 'model': 'mock'} with explanation "Ollama unavailable, fallback mock"
```

Verified 2026-09-05 in WSL: `AI_PROVIDER=ollama` without server → `provider=mock` fallback, no data loss, no crash (see `backend/tests/test_ai.py:1` + manual check). With server running, provider=ollama and raw data not sent beyond aggregated stats.

### 4. Privacy

- **Mock:** no external call, no data leaves machine.
- **Ollama:** HTTP to `OLLAMA_HOST` (default localhost) — stays on your machine or LAN, no cloud.
- **OpenAI:** only if `AI_PROVIDER=openai` and `OPENAI_API_KEY` set — sends prompt (aggregated stats + question, not raw rows) to OpenAI.

### 5. Frontend

`frontend/src/pages/AI.tsx:1` shows `Provider: mock|ollama|openai` per response. No extra config needed; backend handles switch.

## Result

Local-first option is **verified**: `AI_PROVIDER` switch works, fallback is safe, and `qwen2.5:7b` is cached ready for offline use (4.6GB blob at `~/.ollama/models/blobs/sha256-2bada...`).
