"""Pydantic schemas for dataset endpoints."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    created_at: str
    preview: List[dict]  # first 5 rows as dicts


class DatasetInfoResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    dtypes: dict
    created_at: str
    preview: List[dict]


class ColumnTypeInfo(BaseModel):
    column: str
    inferred_type: str
    dtype: str
    missing_count: int
    missing_pct: float
    unique_count: int
    is_constant: bool
    is_empty: bool


class DataQualitySummary(BaseModel):
    n_rows: int
    n_columns: int
    n_numeric: int
    n_categorical: int
    n_date: int
    n_bool: int
    n_text: int
    duplicate_rows: int
    empty_columns: int
    constant_columns: int
    high_cardinality_columns: List[str]
    columns_with_missing: List[str]
    total_missing_values: int
    total_missing_pct: float


class ProfileResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_types: List[ColumnTypeInfo]
    quality_summary: DataQualitySummary
    outlier_flags: List[dict]
    numeric_summary: List[dict]  # numeric_descriptive_summary rows
    categorical_overview: List[dict]


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    detail: Any
    path: Optional[str] = None
