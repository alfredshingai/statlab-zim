"""In-memory dataset store — Milestone 2.

Will be replaced by PostgreSQL in Milestone 3.
Stores DataFrames + metadata keyed by dataset_id (uuid).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

import pandas as pd

# dataset_id -> record
_DATASETS: Dict[str, dict] = {}


def generate_dataset_id() -> str:
    return str(uuid.uuid4())


def save_dataset(
    df: pd.DataFrame,
    filename: str,
    content_type: str | None = None,
) -> dict:
    """Persist DataFrame in memory and return metadata."""
    dataset_id = generate_dataset_id()
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "dataset_id": dataset_id,
        "filename": filename,
        "content_type": content_type,
        "created_at": now,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "dataframe": df,  # keep reference
    }
    _DATASETS[dataset_id] = record
    return record


def get_dataset(dataset_id: str) -> Optional[dict]:
    return _DATASETS.get(dataset_id)


def get_dataframe(dataset_id: str) -> Optional[pd.DataFrame]:
    rec = _DATASETS.get(dataset_id)
    if rec is None:
        return None
    return rec["dataframe"]


def list_datasets() -> Dict[str, dict]:
    return _DATASETS


def delete_dataset(dataset_id: str) -> bool:
    if dataset_id in _DATASETS:
        del _DATASETS[dataset_id]
        return True
    return False


def clear_all() -> None:
    _DATASETS.clear()
