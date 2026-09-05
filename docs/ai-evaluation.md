# AI Evaluation & Failure Documentation — Version 3

**Principle:** AI never invents numbers; all statistics from verified Python engine (`src/stats_tests.py:18`). Evaluation ensures uncertainty is communicated and failures are safe.

## Test Coverage

- `backend/tests/test_ai.py:1` — 6 tests
  - `test_interpret_and_suggest`: keyword → candidate (ttest for "different between groups")
  - `test_ask_full_pipeline`: end-to-end question → interpretation → candidates → verified → mock explanation + provenance
  - `test_explain_verified`: pearson/ttest/chi2 verified results + provider=mock
  - `test_cleaning_suggestions`: missing_values detection + approval note
  - `test_ai_no_fabrication_guarantee`: verified True + statistic from Python, not LLM
  - `test_local_first_option`: `AI_PROVIDER=mock` no network

- `backend/tests/test_ai_report.py:1` — 4 tests
  - `test_ai_report`: title → verified + executive_summary/methods/limitations + provenance
  - `test_ai_report_with_methods`: explicit methods preserved
  - `test_ai_failures_documented`: empty question fallback, invalid columns → verified False with error, mock provider fallback
  - `test_reproducibility`: same input → same statistic/p_value (reproducible)

Total: **30 backend tests** (26 previous + 4) + 19 core = 49.

## Failure Modes Tested & Documented

| Failure | Expected Behavior | Test |
|---|---|---|
| Empty/whitespace question | `interpret_question` returns intent=general, fallback candidates (exploratory descriptive/pearson if feasible) | `test_ai_failures_documented` |
| Insufficient columns (e.g., ttest on 1-col dataset) | `verify_and_calculate` returns `verified=False` + `error` warning, no crash | `test_ai_failures_documented` |
| LLM key missing or Ollama down | `app/ai/llm.py:1` falls back to mock with message, provenance still mock, frontend shows explanation | `test_ai_no_fabrication_guarantee` + `test_local_first_option` |
| Invalid `test_type` | 400 with detail, not 500 | `test_explain_verified` |
| Large CSV (>50MB) or non-UTF8 | `POST /datasets/upload` 400, AI pipeline never runs | `test_milestone2.py` |
| Reproducibility | Same dataset + same test → identical statistic/p_value (no LLM randomness in numbers) | `test_reproducibility` |

## Responsible AI Checklist

- **Provenance:** every `/ai/*` response includes `provenance: All numbers from Python` and `pipeline` string.
- **Uncertainty:** explanations state `p < alpha => Reject H0 else Fail`, mention assumptions, and `Limitations` section.
- **Privacy:** prompts send only aggregated stats (no raw rows); `docs/deploy-free.md` notes raw data stays in Python verification. For offline, set `AI_PROVIDER=ollama` + `OLLAMA_HOST=http://localhost:11434` (no data leaves machine).
- **Destructive ops:** `POST /ai/cleaning-suggest` returns `destructive: true` flagged; UI requires approval before transform.
- **Evaluation in CI:** `backend/tests/test_ai*` run in GitHub Actions; mock provider ensures deterministic CI without API keys.

## To Run Evaluation Locally

```bash
PYTHONPATH=backend pytest backend/tests/test_ai.py backend/tests/test_ai_report.py -v
# Check mock vs openai vs ollama:
AI_PROVIDER=ollama PYTHONPATH=backend pytest backend/tests/test_ai.py::test_local_first_option -v
OPENAI_API_KEY=sk-... AI_PROVIDER=openai PYTHONPATH=backend python -m pytest backend/tests/test_ai.py::test_ask_full_pipeline -v
```
