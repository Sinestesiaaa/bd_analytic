from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def ensure_columns(df: pd.DataFrame, expected_columns: Iterable[str]) -> pd.DataFrame:
    result = df.copy()
    for col in expected_columns:
        if col not in result.columns:
            result[col] = pd.NA
    return result


def list_excel_files(folder: str | Path) -> list[Path]:
    path = Path(folder)
    if not path.exists():
        return []
    return sorted(path.glob("*.xlsx")) + sorted(path.glob("*.xls"))

