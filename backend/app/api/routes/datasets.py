"""Dataset endpoints — Milestone 2.

POST /datasets/upload
GET  /datasets/{dataset_id}
GET  /datasets/{dataset_id}/profile
DELETE /datasets/{dataset_id}
"""

from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.schemas.datasets import DatasetUploadResponse, DatasetInfoResponse, ProfileResponse
from app.services.datasets import (
    dataframe_preview,
    profile_dataframe,
    read_csv_bytes,
    safe_filename,
    validate_csv_filename,
)
from app.store.memory import get_dataset, get_dataframe, save_dataset, delete_dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload CSV dataset",
    description="Upload a CSV file, validate and store in memory (Milestone 2) / DB (Milestone 3). Returns dataset_id for subsequent analyses.",
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV file (UTF-8, comma-separated)"),
    settings: Settings = Depends(get_settings),
):
    # Validate filename
    original_name = file.filename or "dataset.csv"
    filename = safe_filename(original_name)
    try:
        validate_csv_filename(filename, settings.ALLOWED_EXTENSIONS)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Read bytes with size guard
    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
    try:
        df = read_csv_bytes(data, max_bytes=max_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save
    record = save_dataset(df, filename=filename, content_type=file.content_type)
    preview = dataframe_preview(df, n=5)

    return DatasetUploadResponse(
        dataset_id=record["dataset_id"],
        filename=record["filename"],
        rows=record["rows"],
        columns=record["columns"],
        column_names=record["column_names"],
        created_at=record["created_at"],
        preview=preview,
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetInfoResponse,
    summary="Get dataset metadata",
)
async def get_dataset_info(dataset_id: str):
    rec = get_dataset(dataset_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    df: pd.DataFrame = rec["dataframe"]
    preview = dataframe_preview(df, n=5)
    return DatasetInfoResponse(
        dataset_id=rec["dataset_id"],
        filename=rec["filename"],
        rows=rec["rows"],
        columns=rec["columns"],
        column_names=rec["column_names"],
        dtypes=rec["dtypes"],
        created_at=rec["created_at"],
        preview=preview,
    )


@router.get(
    "/{dataset_id}/profile",
    response_model=ProfileResponse,
    summary="Get dataset profile (quality, types, descriptive)",
)
async def get_dataset_profile(dataset_id: str):
    rec = get_dataset(dataset_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    df: pd.DataFrame = rec["dataframe"]
    try:
        prof = profile_dataframe(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profiling failed: {e}")

    return ProfileResponse(
        dataset_id=rec["dataset_id"],
        filename=rec["filename"],
        rows=rec["rows"],
        columns=rec["columns"],
        column_types=prof["column_types"],
        quality_summary=prof["quality_summary"],
        outlier_flags=prof["outlier_flags"],
        numeric_summary=prof["numeric_summary"],
        categorical_overview=prof["categorical_overview"],
    )


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dataset",
)
async def remove_dataset(dataset_id: str):
    ok = delete_dataset(dataset_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    return JSONResponse(status_code=204, content=None)


@router.get(
    "",
    response_model=List[DatasetInfoResponse],
    summary="List all datasets (in-memory)",
)
async def list_all_datasets():
    from app.store.memory import list_datasets

    out = []
    for rec in list_datasets().values():
        df = rec["dataframe"]
        preview = dataframe_preview(df, n=3)
        out.append(
            DatasetInfoResponse(
                dataset_id=rec["dataset_id"],
                filename=rec["filename"],
                rows=rec["rows"],
                columns=rec["columns"],
                column_names=rec["column_names"],
                dtypes=rec["dtypes"],
                created_at=rec["created_at"],
                preview=preview,
            )
        )
    return out
