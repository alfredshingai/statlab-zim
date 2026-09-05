# Free Deployment — Render (Backend) + Vercel (Frontend) + Supabase (Postgres)

Zero-cost stack for StatLab Zim Version 2. All have free tiers suitable for learning/portfolio.

---

## 1. Supabase Postgres (Free 500MB)

1. Create at https://supabase.com → New Project → pick region closest to you (EU for Zimbabwe latency).
2. Project Settings → Database → Connection string → **URI** tab → copy **Pooler** URL (port 6543 for pgBouncer, required for Render):
   ```
   postgresql://postgres.<ref>:<password>@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```
3. For backend, convert to SQLAlchemy URL:
   ```
   postgresql+psycopg2://postgres.<ref>:<password>@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```
   Set as `DATABASE_URL` in Render (see below). Keep password safe.
4. Supabase free pauses after 1 week inactive — wake by visiting dashboard.

---

## 2. Backend — Render (Free)

**Why free:** Render Web Service free sleeps after 15min idle (cold start ~30s), 750h/month free — fine for demo.

1. Go to https://render.com → New → Web Service → Connect `alfredshingai/statlab-zim`.
2. **Option A (Blueprint):** New → Blueprint → select repo → Render reads `render.yaml` → Apply.
   **Option B (Manual):**
   - Root Directory: `.` (repo root)
   - Dockerfile: `backend/Dockerfile`
   - Plan: Free
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (Render overrides Dockerfile CMD)
   - Health Check: `/health`
3. Environment variables (Render Dashboard → Environment):
   ```
   DATABASE_URL=postgresql+psycopg2://postgres.<ref>:...@...pooler.supabase.com:6543/postgres  # from Supabase
   SECRET_KEY=openssl rand -hex 32  → e.g. a1b2c3...  # generate: openssl rand -hex 32
   ENVIRONMENT=production
   DEBUG=false
   BACKEND_CORS_ORIGINS=https://<your-vercel-url>.vercel.app,http://localhost:5173  # set after Vercel
   PYTHONPATH=/app:/app/backend
   ```
4. Deploy → wait → verify:
   ```
   curl https://<render-backend>.onrender.com/health          → {"status":"ok"}
   curl https://<render-backend>.onrender.com/docs            → Swagger UI
   curl https://<render-backend>.onrender.com/api/v1/health   → versioned alias
   ```
5. Note backend URL (e.g. `https://statlab-backend.onrender.com`) for frontend.

---

## 3. Frontend — Vercel (Free Hobby)

1. https://vercel.com → New Project → Import `alfredshingai/statlab-zim` → Framework Preset: Vite → Root Directory: `frontend`.
2. Build settings auto-detected (`npm run build`, output `dist`), or use `vercel.json`.
3. Environment Variable (Vercel → Settings → Environment Variables):
   ```
   VITE_API_URL=https://<render-backend>.onrender.com
   ```
   Must be set **before** build (rebuild if changed).
4. Deploy → Vercel gives `https://statlab-zim.vercel.app` (or custom).
5. Go back to Render → update `BACKEND_CORS_ORIGINS` to include Vercel URL → Redeploy backend (required for CORS).
6. Verify: open Vercel URL → Upload → Descriptive → Tests should call `VITE_API_URL` endpoints.

---

## 4. Local Verification (Same Stack Free)

```bash
# Without Docker (free, no cloud)
cd backend && DATABASE_URL=sqlite:///./statlab.db uvicorn app.main:app --port 8000
cd frontend && VITE_API_URL=http://localhost:8000 npm run dev  # http://localhost:5173

# With Docker (free local)
docker compose up --build
# Frontend http://localhost:5173, Backend http://localhost:8000, Postgres localhost:5432

# Tests (free, no card)
PYTHONPATH=backend pytest backend/tests -v  # 20 passed
PYTHONPATH=. pytest tests -v                 # 19 passed
cd frontend && npm run build                 # vite build ✓
```

---

## 5. Free Tier Limits & Mitigations

- **Render sleep:** first request after idle takes ~30s — show loading spinner (already `st.spinner` in Streamlit, React shows fetch pending).
- **Supabase pause:** auto-pauses after 7 days — wake via dashboard visit; set up UptimeRobot ping to `/health` every 5 days.
- **Vercel hobby:** 100GB bandwidth free — sufficient for student use.

---

## 6. HTTPS/Domain/Logs/Backups (Free)

- HTTPS: auto on Render + Vercel (no config).
- Domain: free `*.onrender.com` + `*.vercel.app`; custom domain free via Vercel.
- Logs: Render Dashboard → Logs; Vercel → Deployments → Logs.
- Backups: Supabase → Database → Backups (daily free); also `pg_dump` local.

---

## 7. After Deploy Checklist

- [ ] `GET /health` returns 200 on Render backend
- [ ] `POST /datasets/upload` via frontend works (CORS OK)
- [ ] Auth `POST /auth/register` → `POST /auth/login` → `GET /projects` (user-specific)
- [ ] `docker compose up` still works locally for dev
- [ ] GitHub Actions CI passes on `origin/main`

**Cost: $0** — stay within free tiers; only pay if you exceed bandwidth/DB size or need no-sleep backend (then $7/month Render Starter).
