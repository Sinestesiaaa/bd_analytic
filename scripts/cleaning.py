from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .utils import ensure_columns, list_excel_files, safe_to_datetime

EXPECTED_COLUMNS = [
    "Date",
    "Model",
    "CN Unit",
    "Description of Breakdown",
    "Hours",
    "Awal",
    "Akhir",
    "Type BD",
    "Shift",
    "HM",
    "Location",
    "PIC Breakdown",
    "PIC Ready",
]

COLUMN_ALIASES = {
    "CN_Unit": "CN Unit",
    "Description_of_Breakdown": "Description of Breakdown",
    "Type_BD": "Type BD",
    "PIC_Breakdown": "PIC Breakdown",
    "PIC_Ready": "PIC Ready",
    "Duration Real": "Duration_Real_Source",
    "Duration_Real": "Duration_Real_Source",
    "Status Severity": "Status_Severity_Source",
    "Status_Severity": "Status_Severity_Source",
}


def load_raw_data(folder: str | Path) -> pd.DataFrame:
    files = list_excel_files(folder)
    if not files:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    frames = []
    for file in files:
        try:
            df = pd.read_excel(file, engine="openpyxl")
            df = df.rename(columns=COLUMN_ALIASES)
            df["source_file"] = file.name
            frames.append(df)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    merged = pd.concat(frames, ignore_index=True)
    return ensure_columns(merged, EXPECTED_COLUMNS + ["source_file"])


def _to_hour_fraction(value: object) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, pd.Timestamp):
        return value.hour + value.minute / 60 + value.second / 3600
    text = str(value).strip()
    if not text:
        return np.nan
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return np.nan
    return parsed.hour + parsed.minute / 60 + parsed.second / 3600


def clean_and_transform(df: pd.DataFrame, duration_tolerance_hours: float = 0.25) -> pd.DataFrame:
    data = ensure_columns(df, EXPECTED_COLUMNS).copy()
    data = data.replace({"(blank)": pd.NA, "": pd.NA})

    data["Date"] = safe_to_datetime(data["Date"]).dt.date
    data["Awal_dt"] = pd.to_datetime(data["Awal"], errors="coerce")
    data["Akhir_dt"] = pd.to_datetime(data["Akhir"], errors="coerce")

    start_hour = data["Awal"].apply(_to_hour_fraction)
    end_hour = data["Akhir"].apply(_to_hour_fraction)
    raw_duration = end_hour - start_hour
    data["Duration_Real"] = np.where(raw_duration < 0, raw_duration + 24, raw_duration)
    data["Duration_Real"] = np.where(
        pd.isna(start_hour) | pd.isna(end_hour), np.nan, data["Duration_Real"]
    )

    data["Hours_Num"] = pd.to_numeric(data["Hours"], errors="coerce")
    diff = (data["Duration_Real"] - data["Hours_Num"]).abs()
    data["Duration_Check"] = np.where(
        pd.isna(data["Duration_Real"]) | pd.isna(data["Hours_Num"]),
        "UNKNOWN",
        np.where(diff <= duration_tolerance_hours, "VALID", "MISMATCH"),
    )

    data["Invalid_Time"] = pd.isna(data["Duration_Real"])
    return data
