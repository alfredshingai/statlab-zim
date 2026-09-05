"""Analysis endpoints — Milestone 2.

POST /analyses/descriptive
POST /analyses/test
"""

import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.schemas.analyses import DescriptiveRequest, DescriptiveResponse, TestRequest
from app.services.analyses import run_descriptive, run_test
from app.store.memory import get_dataframe, get_dataset

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _sanitize(value: Any) -> Any:
    """Convert NaN/Inf to None for JSON."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


@router.post(
    "/descriptive",
    response_model=DescriptiveResponse,
    summary="Descriptive statistics",
    description="Returns numeric summary, categorical overview and frequency tables for a stored dataset.",
)
async def descriptive_analysis(payload: DescriptiveRequest):
    rec = get_dataset(payload.dataset_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Dataset {payload.dataset_id} not found")
    df = get_dataframe(payload.dataset_id)
    assert df is not None
    try:
        result = run_descriptive(df, columns=payload.columns)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Descriptive failed: {e}")

    # Sanitize NaN
    result = _sanitize(result)
    return DescriptiveResponse(
        dataset_id=payload.dataset_id,
        numeric_summary=result["numeric_summary"],
        categorical_overview=result["categorical_overview"],
        frequency_tables=result["frequency_tables"],
    )


@router.post(
    "/test",
    summary="Statistical test",
    description="Run pearson, spearman, linear_regression, ttest, chi2 on a stored dataset. Returns structured JSON with statistic, p_value, decision.",
)
async def statistical_test(payload: TestRequest):
    rec = get_dataset(payload.dataset_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Dataset {payload.dataset_id} not found")
    df = get_dataframe(payload.dataset_id)
    assert df is not None

    # Validate columns exist (basic)
    try:
        result = run_test(
            df,
            test_type=payload.test_type,
            alpha=payload.alpha,
            x_col=payload.x_col,
            y_col=payload.y_col,
            numeric_col=payload.numeric_col,
            group_col=payload.group_col,
            col1=payload.col1,
            col2=payload.col2,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {e}")

    # Sanitize result (NaN -> None, DataFrames -> records)
    sanitized = {}
    for k, v in result.items():
        # Convert pandas DataFrame (contingency) to records
        try:
            import pandas as pd

            if isinstance(v, pd.DataFrame):
                # Convert to dict of dict or list
                v = v.where(pd.notna(v), None).to_dict()
        except Exception:
            pass
        # Convert numpy arrays
        try:
            import numpy as np

            if isinstance(v, np.ndarray):
                v = v.tolist()
        except Exception:
            pass
        sanitized[k] = _sanitize(v)

    # Ensure minimal fields for frontend
    # Return raw sanitized dict (fastapi will json-encode)
    return JSONResponse(content=sanitized)


# Alias for backward compatibility / explicit paths
@router.post("/descriptive/", include_in_schema=False)
async def descriptive_alias(payload: DescriptiveRequest):
    return await descriptive_analysis(payload)


@router.post("/test/", include_in_schema=False)
async def test_alias(payload: TestRequest):
    return await statistical_test(payload)
