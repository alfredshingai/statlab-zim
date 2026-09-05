"""Pydantic schemas for analysis endpoints."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class DescriptiveRequest(BaseModel):
    dataset_id: str = Field(..., description="UUID from /datasets/upload")
    columns: Optional[List[str]] = Field(None, description="Optional subset of columns; default all")


class DescriptiveResponse(BaseModel):
    dataset_id: str
    numeric_summary: List[dict]
    categorical_overview: List[dict]
    frequency_tables: dict  # column -> list of rows


class TestRequest(BaseModel):
    dataset_id: str
    test_type: str = Field(
        ...,
        description="pearson | spearman | linear_regression | ttest | chi2",
        examples=["pearson"],
    )
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    numeric_col: Optional[str] = None
    group_col: Optional[str] = None
    col1: Optional[str] = None
    col2: Optional[str] = None
    alpha: float = Field(0.05, ge=0.001, le=0.5)


class TestResponse(BaseModel):
    test_name: str
    variables: Any
    hypotheses: Optional[dict] = None
    statistic: Any
    p_value: Any
    alpha: float
    n: Optional[int] = None
    decision: str
    interpretation: str
    assumptions: Optional[str] = None
    warnings: List[str] = []
    # extras per test
    extra: Optional[dict] = None
