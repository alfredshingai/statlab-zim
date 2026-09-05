"""Dataset services — CSV parsing + profiling.

Reuses src/ logic (data_quality, descriptive) where available.
Falls back to local implementations if src not importable.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd

# Ensure root src is importable when running backend standalone
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from src.data_quality import column_type_summary, data_quality_summary, basic_outlier_flags
    from src.descriptive import numeric_descriptive_summary, categorical_overview
except Exception:  # pragma: no cover
    # Minimal fallback (should not happen in dev)
    column_type_summary = None  # type: ignore
    data_quality_summary = None  # type: ignore
    basic_outlier_flags = None  # type: ignore
    numeric_descriptive_summary = None  # type: ignore
    categorical_overview = None  # type: ignore


# --- helpers ---

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]")


def safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = SAFE_FILENAME_RE.sub("", name)
    return name[:255] or "dataset.csv"


def validate_csv_filename(filename: str, allowed_exts: list[str]) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in allowed_exts:
        raise ValueError(f"Invalid file extension '{ext}'. Allowed: {allowed_exts}")


def read_csv_bytes(data: bytes, max_bytes: int) -> pd.DataFrame:
    if len(data) > max_bytes:
        raise ValueError(f"File too large: {len(data)} bytes > limit {max_bytes} bytes")
    if not data or data.strip() == b"":
        raise ValueError("Empty file")
    try:
        # Try UTF-8, fallback to latin1? For now strict UTF-8
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"File must be UTF-8 encoded: {e}")
    try:
        df = pd.read_csv(io.StringIO(text))
    except pd.errors.EmptyDataError:
        raise ValueError("Empty CSV: no header found")
    except pd.errors.ParserError as e:
        raise ValueError(f"CSV parse error: {e}")
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")

    if df.columns.duplicated().any():
        # warn but allow; will be surfaced in profile
        pass
    # Enforce header exists
    if len(df.columns) == 0:
        raise ValueError("CSV has no columns")
    return df


def dataframe_preview(df: pd.DataFrame, n: int = 5) -> list[dict]:
    # Convert to JSON-serializable (handle NaN, dates)
    preview = df.head(n).copy()
    # Replace NaN with None for JSON
    preview = preview.where(pd.notna(preview), None)
    # Convert any non-serializable (e.g., Timestamp) to string
    for col in preview.columns:
        # pandas default JSON may handle, but we coerce to python objects
        preview[col] = preview[col].astype(object)
    # Use to_dict
    records = preview.to_dict(orient="records")
    # Ensure values are JSON-serializable (convert numpy types)
    import numpy as np

    def _convert(v):
        if isinstance(v, (np.integer, np.int64)):
            return int(v)
        if isinstance(v, (np.floating, np.float64)):
            if np.isnan(v):
                return None
            return float(v)
        if pd.isna(v):
            return None
        return v

    clean = []
    for r in records:
        clean.append({k: _convert(v) for k, v in r.items()})
    return clean


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Return profiling dict using src utilities."""
    if column_type_summary is None:
        raise RuntimeError("Profiling utilities not available")
    type_sum = column_type_summary(df)
    quality = data_quality_summary(df)
    outliers = basic_outlier_flags(df)
    numeric_sum = numeric_descriptive_summary(df)
    cat_over = categorical_overview(df)

    # Convert DataFrames to list-of-dicts with NaN -> None
    def df_to_records(dframe: pd.DataFrame) -> list[dict]:
        if dframe.empty:
            return []
        # Replace NaN/NaT
        import numpy as np

        recs = dframe.where(pd.notna(dframe), None).to_dict(orient="records")
        out = []
        for r in recs:
            nr = {}
            for k, v in r.items():
                if isinstance(v, float) and np.isnan(v):
                    nr[k] = None
                elif isinstance(v, (np.integer, np.floating)):
                    nr[k] = float(v) if isinstance(v, np.floating) else int(v)
                else:
                    nr[k] = v
            out.append(nr)
        return out

    return {
        "column_types": df_to_records(type_sum),
        "quality_summary": quality,
        "outlier_flags": df_to_records(outliers),
        "numeric_summary": df_to_records(numeric_sum),
        "categorical_overview": df_to_records(cat_over),
    }
