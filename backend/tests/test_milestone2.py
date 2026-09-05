"""Milestone 2 — Statistical API integration tests."""

import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store.memory import clear_all

client = TestClient(app)

SAMPLE_CSV = """age,income,gender,score
24,34000,M,78
31,52000,F,85
27,,F,92
45,60000,M,88
22,28000,F,76
"""

SAMPLE_CSV_2 = """x,y,group,cat1,cat2
1,2,A,a,p
2,4,A,a,q
3,6,B,b,p
4,8,B,b,q
5,10,A,a,p
6,12,B,b,q
"""


def _upload(csv_text: str, filename: str = "test.csv"):
    return client.post(
        "/datasets/upload",
        files={"file": (filename, io.BytesIO(csv_text.encode("utf-8")), "text/csv")},
    )


@pytest.fixture(autouse=True)
def clean_store():
    clear_all()
    yield
    clear_all()


def test_upload_and_get():
    r = _upload(SAMPLE_CSV)
    assert r.status_code == 201, r.text
    data = r.json()
    assert "dataset_id" in data
    assert data["rows"] == 5
    assert data["columns"] == 4
    assert len(data["preview"]) == 5

    ds_id = data["dataset_id"]
    r2 = client.get(f"/datasets/{ds_id}")
    assert r2.status_code == 200
    assert r2.json()["dataset_id"] == ds_id
    assert r2.json()["rows"] == 5

    # versioned alias
    r3 = client.get(f"/api/v1/datasets/{ds_id}")
    assert r3.status_code == 200


def test_profile():
    r = _upload(SAMPLE_CSV)
    ds_id = r.json()["dataset_id"]
    pr = client.get(f"/datasets/{ds_id}/profile")
    assert pr.status_code == 200
    j = pr.json()
    assert j["dataset_id"] == ds_id
    assert "column_types" in j
    assert "quality_summary" in j
    assert "numeric_summary" in j
    # check types
    assert any(c["column"] == "age" for c in j["column_types"])


def test_descriptive():
    r = _upload(SAMPLE_CSV_2)
    ds_id = r.json()["dataset_id"]
    payload = {"dataset_id": ds_id}
    res = client.post("/analyses/descriptive", json=payload)
    assert res.status_code == 200, res.text
    j = res.json()
    assert j["dataset_id"] == ds_id
    assert "numeric_summary" in j
    assert "categorical_overview" in j
    # check numeric_summary has x/y
    vars_found = [row["variable"] for row in j["numeric_summary"]]
    assert "x" in vars_found

    # versioned
    res2 = client.post("/api/v1/analyses/descriptive", json=payload)
    assert res2.status_code == 200


def test_pearson():
    r = _upload(SAMPLE_CSV_2)
    ds_id = r.json()["dataset_id"]
    payload = {
        "dataset_id": ds_id,
        "test_type": "pearson",
        "x_col": "x",
        "y_col": "y",
        "alpha": 0.05,
    }
    res = client.post("/analyses/test", json=payload)
    assert res.status_code == 200, res.text
    j = res.json()
    assert j["test_name"] == "Pearson correlation"
    assert "p_value" in j
    assert j["decision"] in ["Reject H0", "Fail to reject H0", "Inconclusive"]


def test_spearman_regression_ttest_chi2():
    r = _upload(SAMPLE_CSV_2)
    ds_id = r.json()["dataset_id"]

    # spearman
    res = client.post(
        "/analyses/test",
        json={"dataset_id": ds_id, "test_type": "spearman", "x_col": "x", "y_col": "y"},
    )
    assert res.status_code == 200
    assert "Spearman" in res.json()["test_name"]

    # regression
    res = client.post(
        "/analyses/test",
        json={"dataset_id": ds_id, "test_type": "linear_regression", "x_col": "x", "y_col": "y"},
    )
    assert res.status_code == 200
    assert "regression" in res.json()["test_name"].lower()

    # ttest: y numeric, group categorical
    res = client.post(
        "/analyses/test",
        json={"dataset_id": ds_id, "test_type": "ttest", "numeric_col": "y", "group_col": "group"},
    )
    assert res.status_code == 200
    assert "t-test" in res.json()["test_name"]

    # chi2
    res = client.post(
        "/analyses/test",
        json={"dataset_id": ds_id, "test_type": "chi2", "col1": "cat1", "col2": "cat2"},
    )
    assert res.status_code == 200
    assert "Chi-square" in res.json()["test_name"]


def test_error_handling():
    # invalid dataset_id
    res = client.get("/datasets/not-exist")
    assert res.status_code == 404
    assert res.json()["error"] == "http_error"

    # invalid upload (wrong extension)
    r = client.post("/datasets/upload", files={"file": ("test.txt", io.BytesIO(b"a,b\n1,2"), "text/plain")})
    assert r.status_code == 400

    # empty file
    r = client.post("/datasets/upload", files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")})
    assert r.status_code == 400

    # too large simulation via direct service check (not via http, but ensure config)
    from app.core.config import get_settings

    assert get_settings().MAX_UPLOAD_SIZE_BYTES > 0


def test_list_and_delete():
    r1 = _upload(SAMPLE_CSV, "a.csv")
    r2 = _upload(SAMPLE_CSV_2, "b.csv")
    list_r = client.get("/datasets")
    assert list_r.status_code == 200
    assert len(list_r.json()) == 2

    ds_id = r1.json()["dataset_id"]
    del_r = client.delete(f"/datasets/{ds_id}")
    assert del_r.status_code == 204
    assert client.get(f"/datasets/{ds_id}").status_code == 404
