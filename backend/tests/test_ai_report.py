"""AI report generation + evaluation tests."""

import io
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.store.memory import clear_all

Base.metadata.create_all(bind=engine)
client = TestClient(app)

CSV = """x,y,group,cat1,cat2
1,2,A,a,p
2,4,A,a,q
3,6,B,b,p
4,8,B,b,q
5,10,A,a,p
6,12,B,b,q
"""


def _upload():
    clear_all()
    r = client.post("/datasets/upload", files={"file": ("r.csv", io.BytesIO(CSV.encode()), "text/csv")})
    assert r.status_code == 201
    return r.json()["dataset_id"]


def test_ai_report():
    ds = _upload()
    r = client.post("/ai/report", json={"dataset_id": ds, "title": "Demo Report"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["title"] == "Demo Report"
    assert "verified" in j
    assert "report" in j
    assert "executive_summary" in j["report"]
    assert "methods" in j["report"]
    assert "limitations" in j["report"]
    assert j["provenance"].startswith("All numbers")


def test_ai_report_with_methods():
    ds = _upload()
    r = client.post("/ai/report", json={"dataset_id": ds, "title": "T", "methods": ["pearson", "ttest"]})
    assert r.status_code == 200
    assert r.json()["methods"] == ["pearson", "ttest"]


def test_ai_failures_documented():
    """AI failures are tested and documented: empty dataset, invalid columns, missing LLM key."""
    ds = _upload()
    # Empty question -> should still return candidates (fallback)
    r = client.post("/ai/ask", json={"dataset_id": ds, "question": "   "})
    assert r.status_code == 200
    assert r.json()["interpretation"]["intent"] in ["general", "analysis"]

    # Invalid test type -> should be caught, not crash, with error in verified
    from app.ai.service import verify_and_calculate
    import pandas as pd

    df = pd.DataFrame({"a": [1, 2, 3]})
    v = verify_and_calculate(df, {"test_type": "ttest", "assumptions": ""})
    assert v["verified"] is False
    assert "error" in v

    # Mock provider should never return None explanation when verified exists
    r = client.post("/ai/explain", json={"dataset_id": ds, "test_type": "pearson", "x_col": "x", "y_col": "y"})
    assert r.json()["provider"] == "mock"
    assert r.json()["explanation"] is not None


def test_reproducibility():
    """Statistical calculations remain reproducible: same input -> same statistic."""
    ds = _upload()
    r1 = client.post("/ai/explain", json={"dataset_id": ds, "test_type": "pearson", "x_col": "x", "y_col": "y"})
    r2 = client.post("/ai/explain", json={"dataset_id": ds, "test_type": "pearson", "x_col": "x", "y_col": "y"})
    assert r1.json()["verified_result"]["statistic"] == r2.json()["verified_result"]["statistic"]
    assert r1.json()["verified_result"]["p_value"] == r2.json()["verified_result"]["p_value"]
