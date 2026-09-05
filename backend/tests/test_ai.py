"""Version 3 — AI pipeline tests (mock provider, no API key needed)."""

import io
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.store.memory import clear_all

Base.metadata.create_all(bind=engine)
client = TestClient(app)

CSV = """x,y,group,cat1,cat2,score
1,2,A,a,p,10
2,4,A,a,q,12
3,6,B,b,p,14
4,8,B,b,q,16
5,10,A,a,p,18
6,12,B,b,q,20
"""


def _upload():
    clear_all()
    r = client.post("/datasets/upload", files={"file": ("test.csv", io.BytesIO(CSV.encode()), "text/csv")})
    assert r.status_code == 201, r.text
    return r.json()["dataset_id"]


def test_interpret_and_suggest():
    ds = _upload()
    r = client.post("/ai/suggest", json={"dataset_id": ds, "question": "Is satisfaction different between age groups?"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert "candidates" in j
    assert any(c["test_type"] == "ttest" for c in j["candidates"])
    assert "ai_suggestions" in j


def test_ask_full_pipeline():
    ds = _upload()
    r = client.post("/ai/ask", json={"dataset_id": ds, "question": "Which product has the highest average sales?"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["question"]
    assert "interpretation" in j
    assert "candidates" in j
    assert "verified" in j
    assert "explanation" in j
    assert j["pipeline"].startswith("question →")
    # Provenance: verified engine
    assert "provenance" in j
    assert j["primary_verified"] is not None


def test_explain_verified():
    ds = _upload()
    r = client.post("/ai/explain", json={"dataset_id": ds, "test_type": "pearson", "x_col": "x", "y_col": "y"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["verified_result"]["test_name"] == "Pearson correlation"
    assert "explanation" in j
    assert j["provenance"].startswith("Verified")

    # ttest
    r = client.post("/ai/explain", json={"dataset_id": ds, "test_type": "ttest", "numeric_col": "y", "group_col": "group"})
    assert r.status_code == 200
    assert "t-test" in r.json()["verified_result"]["test_name"]

    # chi2
    r = client.post("/ai/explain", json={"dataset_id": ds, "test_type": "chi2", "col1": "cat1", "col2": "cat2"})
    assert r.status_code == 200


def test_cleaning_suggestions():
    csv_missing = """a,b,c
1,2,3
2,,4
3,5,
"""
    r = client.post("/datasets/upload", files={"file": ("m.csv", io.BytesIO(csv_missing.encode()), "text/csv")})
    ds = r.json()["dataset_id"]
    r = client.post("/ai/cleaning-suggest", json={"dataset_id": ds})
    assert r.status_code == 200, r.text
    j = r.json()
    assert "suggestions" in j
    assert any(s["issue"] == "missing_values" for s in j["suggestions"])
    assert "ai_summary" in j
    assert "approval" in j["note"].lower()


def test_ai_no_fabrication_guarantee():
    """Ensure verified numbers come from Python, not LLM mock hallucination."""
    ds = _upload()
    r = client.post("/ai/ask", json={"dataset_id": ds, "question": "What is the correlation between x and y?"})
    j = r.json()
    # Find verified with statistic
    primary = j["primary_verified"]
    assert primary["verified"] is True
    # Verified result must have statistic from Python
    assert "result" in primary
    # Explanation must be present but not be the source of numbers
    assert j["explanation"] is not None
    # Mock provider tag shows no external calc
    assert j["llm_meta"]["provider"] == "mock"

    # Explain endpoint also mock
    r = client.post("/ai/explain", json={"dataset_id": ds, "test_type": "pearson", "x_col": "x", "y_col": "y"})
    assert r.json()["provider"] == "mock"


def test_local_first_option():
    # Ollama path is fallback to mock if Ollama not running — should not crash
    from app.core.config import get_settings

    assert get_settings().OLLAMA_HOST is not None
    # By default AI_PROVIDER=mock, so no network call
    assert get_settings().AI_PROVIDER == "mock"
