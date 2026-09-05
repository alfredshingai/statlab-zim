# 📊 StatLab Zim

> **Live App:** https://statlab-zim.streamlit.app — Upload a CSV and explore your data in seconds.

StatLab Zim is a web application for **learning and applying basic statistics** — built for students, researchers, and small businesses in Zimbabwe and beyond. Upload any CSV dataset to explore its structure, run descriptive analyses, visualize distributions and relationships, and perform common statistical tests — all with plain-language interpretations and one-click exports.

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit 1.62](https://img.shields.io/badge/Streamlit-1.62-red)
![FastAPI 0.141](https://img.shields.io/badge/FastAPI-0.141-green)
![React 19](https://img.shields.io/badge/React-19-blue)
![Tests](https://img.shields.io/badge/tests-49%20passed-brightgreen)
![Frontend](https://img.shields.io/badge/frontend%20tests-3%20passed-brightgreen)
![License MIT](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### Milestones 1–6 — Core App
- **Upload & Preview:** Drag-and-drop CSV upload (UTF-8, comma-separated), header validation, empty-file handling
- **Dataset Overview:** Row/column counts, missing-value counts, duplicate detection, column types & unique values
- **Data Quality Dashboard:** Per-column `inferred_type` (numeric/categorical/date/bool/text), missing %, constant/empty flags, high-cardinality detection (>50 uniques), IQR outlier flags

### Milestone 6 — Descriptive Statistics
- **Numeric Summary:** Count, mean, median, std (ddof=1), var, min, max, Q1 (25%), Q2 (50%), Q3 (75%), IQR, **skewness**, **kurtosis**, **CV %** — rounded display + full-precision CSV
- **Categorical Summary:** Per-column `n_categories`, `most_common` value + count, plus per-column **frequency table** (`Category, Count, Proportion, Percentage`) and download

### Milestone 7 — Visualizations
- **Histogram** — numeric selector + bins slider (5–100)
- **Boxplot** — median, quartiles, whiskers, outliers
- **Bar Chart** — categorical frequency
- **Scatter Plot** — X/Y numeric selectors with same-variable guard
- **Line Chart** — date + value columns (auto-detects `datetime64` + coerces string dates >50% parseable)
- **Correlation Heatmap** — `RdBu_r`, `zmin=-1/zmax=1`, `text_auto=True` + correlation matrix table

All charts are **interactive Plotly** (zoom, pan, hover) with **optional PNG export** via `kaleido` (graceful fallback if Chrome not installed).

### Milestone 8 — Statistical Tests
Each test shows: **test name, variables, H₀/H₁, statistic, p-value, alpha, decision (Reject/Fail), interpretation, assumptions, warnings**

| Test | Variables | Method |
|------|-----------|--------|
| **Pearson correlation** | 2 numeric | `scipy.stats.pearsonr` — linear correlation |
| **Spearman correlation** | 2 numeric/ordinal | `scipy.stats.spearmanr` — rank/monotonic |
| **Simple linear regression** | X numeric → Y numeric | `scipy.stats.linregress` — slope, intercept, R², trendline |
| **Independent t-test** | numeric + 2-group categorical | `scipy.stats.ttest_ind` (Welch, `equal_var=False`) |
| **Chi-square** | 2 categorical | `scipy.stats.chi2_contingency` — observed vs expected |

Global `α` slider in sidebar (0.01–0.10) + per-test override.

### Milestone 9 — Export/Download
- **Dataset:** uploaded CSV
- **Column info, numeric/categorical summaries, frequency tables** — CSV
- **Data Quality:** `statlab_column_quality_summary.csv` + `statlab_data_quality_summary.csv` (high-level metrics) + `statlab_outlier_flags.csv`
- **Correlation matrix** — CSV
- **Statistical tests:** single-test CSV + **combined** `statlab_all_test_results.csv`
- **Charts:** PNG via `fig.to_image(format="png", scale=2)` (optional)

### Milestone 10 — Tests
~19 `pytest` tests covering: row/col counts, missing-value %, duplicate detection, numeric-column detection, descriptive spot-checks, empty/invalid file handling, high-cardinality, outlier flags, CSV & PNG exports. Run: `pytest -v`.

### Milestone 11 — Polish
- Emoji headings, `help=` tooltips on every selector, `st.spinner` on heavy ops, friendly empty-states (`No numeric columns found… check formatting`), `st.success`/`st.warning` health indicators, improved variable selection (placeholder, help, columns layout), duplicate-column & header-only warnings, parser error handling.

---

## 🖼️ Screenshots

| Page | Preview |
|------|---------|
| **Overview** | ![Overview](screenshots/overview.png) |
| **Descriptive Statistics** | ![Descriptive](screenshots/descriptive.png) |
| **Visualizations** | ![Visualizations](screenshots/visualizations.png) |
| **Statistical Tests** | ![Statistical Tests](screenshots/stats_tests.png) |
| **Data Quality** | ![Data Quality](screenshots/data_quality.png) |

> Screenshots are auto-generated placeholders. Replace with real captures via `screenshots/README.md` instructions.

---

## 🚀 Usage

### Installation

```bash
git clone https://github.com/alfredshingai/statlab-zim.git
cd statlab-zim

python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Run Locally

```bash
streamlit run app.py
# → Local URL: http://localhost:8501
```

### Using the App

1. **Open** http://localhost:8501 (or the **Live App** link above).
2. **Upload** a CSV file (first row = header, comma-separated, UTF-8).
3. **Navigate** via sidebar:
   - **Overview** — preview + health check (missing/duplicates)
   - **Descriptive Statistics** — numeric & categorical tables + downloads
   - **Visualizations** — histogram/boxplot/bar/scatter/line/heatmap + PNG
   - **Statistical Tests** — Pearson, Spearman, regression, t-test, chi-square + interpretations + CSVs
   - **Data Quality** — type summary, outlier flags, high-cardinality warnings + exports
4. **Download** results via `⬇️` buttons next to each table/chart.

### Example CSV

```csv
age,income,gender,date,score
24,34000,M,2023-01-01,78
31,52000,F,2023-01-02,85
27,,F,2023-01-03,92
```

---

## 🧮 Methods & Formulas

- **Mean:** `Σx / n` · **Median:** 50th percentile · **Std/Var:** sample (`ddof=1`)
- **Quartiles:** `quantile(0.25)`, `0.50`, `0.75` · **IQR:** `Q3 − Q1`
- **Skewness:** `pandas.Series.skew()` · **Kurtosis:** `pandas.Series.kurt()` (Fisher excess, 0 = normal)
- **CV:** `std / mean × 100%` (NaN if mean=0)
- **Pearson r:** `pearsonr(x,y)` — tests H₀: r=0, decision: p<α ⇒ Reject
- **Spearman ρ:** `spearmanr(x,y)` — rank-based, robust to outliers
- **Linear regression:** `linregress(x,y)` → slope, intercept, `r²`, `p`, `stderr`, `slope/se` statistic; equation `y = slope·x + intercept`
- **Welch t-test:** `ttest_ind(g1,g2,equal_var=False)` — H₀: means equal
- **Chi-square:** `chi2_contingency(contingency)` → χ², p, dof, expected; warning if expected <5

**Assumptions shown in UI:** normality/linearity for Pearson, monotonic for Spearman, linearity/homoscedasticity/normal residuals for regression, normality per group for t-test, `expected ≥5` for chi-square.

---

## ⚠️ Limitations

- **Not a replacement for expert statistical advice** — results are educational; check assumptions (e.g., residual plots, normality) beyond the app.
- **CSV only** (`.csv`), UTF-8, comma-delimited, header required; Excel, large files (>200 MB), or non-UTF-8 may fail — see error banner guidance.
- **Missing data:** handled via `dropna` per analysis; no imputation. Columns with all missing are flagged as empty.
- **Date parsing:** auto-detects `datetime64` or coerces string dates if >50% parseable; ambiguous formats (e.g., `01/02/03`) may mis-parse — use ISO `YYYY-MM-DD`.
- **High-cardinality:** categorical columns >50 uniques flagged; chi-square with sparse cells warns `expected <5`.
- **Constant / low-n:** constant variables give `NaN` correlations, warnings; tests need ≥3 observations (≥2 per group for t-test/ANOVA).
- **PNG export:** requires `kaleido` 1.4+ with Chrome (`plotly_get_chrome`). If Chrome missing, PNG buttons show fallback caption — CSVs always work.
- **Performance:** in-memory `pandas`; very large datasets (>500k rows) may be slow on Streamlit Community Cloud (1 GB RAM limit).

---

## 🏗️ Project Structure

```
statlab-zim/
├── app.py                 # Streamlit app — 5 pages, spinners, downloads, polished UI (Version 1)
├── requirements.txt       # streamlit, pandas, numpy, scipy, statsmodels, plotly, kaleido, pytest
├── src/
│   ├── data_quality.py    # is_numeric/categorical/date, column_type_summary, data_quality_summary
│   ├── descriptive.py     # numeric_descriptive_summary, categorical_frequency_table/overview
│   ├── visualizations.py  # histogram/box/bar/scatter/line/heatmap + column helpers
│   ├── stats_tests.py     # pearson/spearman/linear/t_test/chi2 with full reporting dicts
│   └── export.py          # CSV/PNG export utilities (Milestone 9)
├── backend/               # Version 2 — FastAPI backend (Milestones 1-3,5,7)
│   ├── app/
│   │   ├── main.py        # FastAPI + lifespan DB init, health, datasets, analyses, auth, projects, reports
│   │   ├── core/config.py # env vars + DB + auth + CORS
│   │   ├── core/security.py # bcrypt + JWT
│   │   ├── db/base.py, models.py, session.py # SQLAlchemy + Postgres/SQLite
│   │   ├── api/routes/health.py, datasets.py, analyses.py, auth.py, projects.py, reports.py
│   │   ├── services/datasets.py, analyses.py # reuse src/ logic
│   │   └── store/memory.py # in-memory until DB migration completes
│   ├── tests/test_health.py (7) + test_milestone2.py (7) + test_db.py (4) + test_auth.py (2)
│   ├── requirements.txt   # fastapi, sqlalchemy, passlib, python-jose
│   ├── Dockerfile         # root-context build
│   └── .env.example
├── frontend/              # Version 2 — React + TypeScript (Milestone 4)
│   ├── src/pages/Landing.tsx, Dashboard.tsx, Upload.tsx, DatasetOverview.tsx, Descriptive.tsx, Tests.tsx, Charts.tsx, Projects.tsx, Reports.tsx, Auth.tsx
│   ├── src/api/client.ts  # REST client for FastAPI
│   ├── src/components/Layout.tsx
│   └── vite.config.ts     # proxy to FastAPI
├── docker-compose.yml     # db (postgres), backend, frontend
├── .github/workflows/ci.yml # backend + frontend CI
├── tests/
│   └── test_data_quality.py # 19 tests
├── screenshots/
├── data/ docs/ notebooks/ # reserved
└── .streamlit/config.toml
```

### Version 2 — Full-stack Roadmap

Version 1 Streamlit MVP ✅ complete. Version 2 milestones progression:

**Milestone 1: Backend foundation — ✅ Complete**
- `backend/app/main.py:1` + `backend/app/api/routes/health.py:1` `GET /health` & `GET /api/v1/health`, `/docs`, `/redoc`, `/openapi.json`, CORS, `X-Process-Time`, error handlers (404/422/500)
- `backend/app/core/config.py:1` env vars + `backend/.env.example:1`

**Milestone 2: Statistical API — ✅ Complete**
- `POST /datasets/upload` → `GET /datasets/{id}` → `GET /datasets/{id}/profile` (`backend/app/api/routes/datasets.py:1`), `POST /analyses/descriptive` + `POST /analyses/test` (`backend/app/api/routes/analyses.py:1`)
- Reuses `src/data_quality.py:1`, `src/descriptive.py:1`, `src/stats_tests.py:18` via `backend/app/services/*.py`; size limits, safe filenames, validation
- Verified `20 backend tests` (health 7 + milestone2 7 + db 4 + auth 2) + 19 core = 39 total

**Milestone 3: Database — ✅ Complete**
- `backend/app/db/models.py:1` tables: `users`, `datasets`, `projects`, `analysis_results`, `reports` with PK/FK, indexes (`ix_users_email`, `ix_datasets_owner`, etc.), timestamps, relationships, transactions
- `backend/app/db/session.py:1` SQLite dev (`sqlite:///./statlab.db`) + Postgres prod (`postgresql+psycopg2`), `Base.metadata.create_all` in lifespan

**Milestone 4: React frontend — ✅ Complete (scaffold)**
- Vite + React 19 + TS + react-router-dom (`frontend/src/App.tsx:1`), 10 pages: Landing, Dashboard, Upload, Dataset overview, Descriptive, Tests, Charts, Projects, Reports, Auth
- `frontend/src/api/client.ts:1` talks to FastAPI; `vite.config.ts:1` proxies `/health`, `/datasets`, `/analyses`, `/auth`, `/projects`, `/reports` to `localhost:8000`; build passes (`npm run build` → 249kB)

**Milestone 5: Authentication — ✅ Complete**
- `backend/app/core/security.py:1` bcrypt + `python-jose` JWT, `backend/app/api/routes/auth.py:1` `POST /auth/register` (EmailStr, ≥8 chars), `POST /auth/login` (OAuth2), `GET /auth/me`, `POST /auth/logout`, protected `GET /projects` + `POST /projects` per user

**Milestone 6: File storage — ✅ Complete (Milestone 2 + config)**
- `MAX_UPLOAD_SIZE_MB=50`, `ALLOWED_EXTENSIONS=[".csv"]`, `safe_filename` sanitization, UTF-8 check, size guard, `DELETE /datasets/{id}`; object storage path reserved (`file_path` in `Dataset` model)

**Milestone 7: Reports — ✅ Complete (backend)**
- `backend/app/api/routes/reports.py:1` `POST /reports/generate` + `GET /reports` with project title, dataset info, methods, results, charts, interpretation, limitations, creation date; `Report` model persisted

**Milestone 8: Testing & CI — ✅ Complete**
- Backend: `backend/tests/test_health.py`, `test_milestone2.py`, `test_db.py`, `test_auth.py` (20 tests); Frontend: `tsc --noEmit` + `vite build`; `.github/workflows/ci.yml:1` runs both on push/PR

**Milestone 9: Deployment — ✅ Complete (config)**
- `backend/Dockerfile:1` (root-context), `frontend/Dockerfile:1` (multi-stage nginx), `docker-compose.yml:1` (postgres 16 + backend + frontend), `render.yaml:1`, `vercel.json:1`, `docs/deploy-free.md:1` (Render+Vercel+Supabase free)

### Version 3 — AI StatLab (Foundation + Report Generation + Polish — ✅ Complete Core)
- **Architecture:** `Question → interpretation → candidate selection → Python verification → AI explanation → answer` (`backend/app/ai/service.py:1`). AI never calculates; `backend/app/ai/llm.py:1` mock / openai / ollama local-first
- **Endpoints:** `POST /ai/ask` (full pipeline), `POST /ai/suggest`, `POST /ai/explain` (means/p-values/effects/assumptions), `POST /ai/cleaning-suggest` (approval-gated), `POST /ai/report` (exec summary/methods/results/limitations, verified numbers) (`backend/app/api/routes/ai.py:1`, `backend/app/ai/report.py:1`), `GET /reports/{id}/html` & `/download` (`backend/app/api/routes/reports.py:1`)
- **Frontend:** `frontend/src/pages/AI.tsx:1` polished — candidate cards (Feasible badge), verified cards (statistic/p-value/decision + diff view), streaming explanation, cleaning approval checkboxes; `frontend/src/pages/Reports.tsx:1` AI report preview + print/PDF; proxies `/ai` via `vite.config.ts:1`
- **Config:** `AI_PROVIDER=mock|openai|ollama` (`backend/app/core/config.py:1`), `backend/.env.example:1`
- **Evaluation:** `backend/tests/test_ai.py:1` 6 + `backend/tests/test_ai_report.py:1` 4 =10 AI tests; `frontend/src/__tests__/AI.test.tsx:1` (Vitest) 3 frontend tests; `docs/ai-evaluation.md:1` failure modes, provenance, reproducibility, privacy; `docs/deploy-free.md:1` Ollama offline; CI includes Vitest `.github/workflows/ci.yml:1`
- **Verified:** total backend `30 tests` + core 19 + frontend 3 =52 (49 backend+core +3 frontend)

---

## 🧪 Testing

```bash
# Version 1 — Streamlit core (19 tests)
PYTHONPATH=. pytest tests -v

# Version 2 + 3 — Backend (30 tests: health 7 + milestone2 7 + db 4 + auth 2 + ai 10)
PYTHONPATH=backend pytest backend/tests -v
PYTHONPATH=backend pytest backend/tests/test_ai.py backend/tests/test_ai_report.py -v  # Version 3 AI

# Frontend typecheck + build + Vitest (3 tests)
cd frontend && npm run build && npm test && npx tsc --noEmit

# All (52 tests: 49 backend+core +3 frontend)
PYTHONPATH=. pytest tests -v && PYTHONPATH=backend pytest backend/tests -v && cd frontend && npm test

.venv/bin/python -m py_compile app.py src/*.py
PYTHONPATH=backend python -m py_compile backend/app/*.py backend/app/**/*.py backend/app/ai/*.py
```

Tests cover: row/col counts, missing-value % (including `is_empty` columns), `duplicate_row_count`, `is_numeric_series` (bool excluded), descriptive spot-checks (mean/median/Q1/Q3/IQR/std/var/CV with `pytest.approx`), constant-column handling, categorical frequency proportions, empty DataFrames (0 rows/0 cols), header-only CSVs, invalid CSVs, high-cardinality (>50), outlier IQR flags, and export CSV/PNG.

---

## ☁️ Deployment

### Streamlit Cloud (Version 1)

1. **Push to GitHub** (already at `alfredshingai/statlab-zim`):
   ```bash
   git add README.md requirements.txt app.py src/ tests/ screenshots/ .streamlit/
   git commit -m "Milestone 12: expand README, screenshots, deploy"
   git push origin main
   ```
2. **Deploy** on [share.streamlit.io](https://share.streamlit.io):
   - **New app** → Repository: `alfredshingai/statlab-zim` → Branch: `main` → Main file: `app.py`
   - Add `Python 3.12` in **Advanced settings** → **Deploy**
3. **Live link:** `https://statlab-zim.streamlit.app`

### Full-stack (Version 2) — Docker + Compose

```bash
# Local full-stack
docker compose up --build
# Frontend http://localhost:5173 → proxies to backend http://localhost:8000
# Backend docs http://localhost:8000/docs, health http://localhost:8000/health
# Postgres at localhost:5432 (statlab/statlabpass)

# Env overrides
DATABASE_URL=postgresql+psycopg2://statlab:statlabpass@db:5432/statlab \
SECRET_KEY=prod-secret \
BACKEND_CORS_ORIGINS=http://localhost:5173,https://yourdomain.com \
docker compose up

# Frontend alone (dev)
cd frontend && npm install && npm run dev  # http://localhost:5173
# Backend alone (dev)
cd backend && uvicorn app.main:app --reload --port 8000
```

Production: set `ENVIRONMENT=production`, `DEBUG=false`, `SECRET_KEY`, `DATABASE_URL`, `VITE_API_URL=https://api.yourdomain.com`, configure HTTPS, backups, logs, and error monitoring via provider (e.g., Railway/Render/Fly + Supabase/Never).

---

## 🛠️ Tech Stack

- **Python 3.12** · **Streamlit 1.62** · **FastAPI 0.141** · **React 19 + Vite** · **pandas 2.2** · **numpy 2.0** · **scipy 1.14** · **statsmodels 0.14** · **plotly 7.0** · **kaleido 1.4** · **Pillow 11** · **pytest 8.3 + Vitest**
- **Backend:** `pydantic-settings`, `uvicorn`, `sqlalchemy`, `passlib`/`bcrypt`, `python-jose`, `openai`/`httpx` (AI)
- **Frontend:** `react-router-dom`, `axios`, `@testing-library/react`, `jsdom`
- **Lint/Format:** `py_compile` + `tsc --noEmit` + Vitest + CI

---

## 📄 License

MIT — see `LICENSE` (if missing, considered MIT as per original README).

## 🙏 Acknowledgements

Built for learners in Zimbabwe — inspired by ZIMSTAT open data and introductory stats courses. Contributions welcome via Issues/PRs.

---

**Questions?** Open an Issue at https://github.com/alfredshingai/statlab-zim/issues or use the app's sidebar tip.
