from __future__ import annotations

from datetime import time

import pandas as pd

CATEGORY_KEYWORDS = {
    "ENGINE": ["ENGINE"],
    "LUBRICATION": ["OIL", "LUBE"],
    "HYDRAULIC": ["HOSE", "HYDRAULIC"],
    "COOLING": ["COOLANT", "RADIATOR"],
    "UNDERCARRIAGE": ["BOLT", "TRACK", "CHAIN"],
    "FUEL SYSTEM": ["FUEL", "INJECTOR"],
    "ATTACHMENT": ["ARM", "BUCKET"],
}


def classify_category(text: object) -> str:
    if pd.isna(text):
        return "OTHER"
    value = str(text).upper()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in value for keyword in keywords):
            return category
    return "OTHER"


def add_classification_columns(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["Category"] = data["Description of Breakdown"].apply(classify_category)

    duration = pd.to_numeric(data.get("Duration_Real"), errors="coerce")
    data["Severity"] = pd.cut(
        duration,
        bins=[-float("inf"), 2, 6, float("inf")],
        labels=["Minor", "Medium", "Major"],
        right=False,
    ).astype("object")
    data["Severity"] = data["Severity"].fillna("Unknown")
    if "Status_Severity_Source" in data.columns:
        src = data["Status_Severity_Source"].astype("string").str.strip()
        data["Severity"] = data["Severity"].where(src.isna(), src)

    date_ts = pd.to_datetime(data["Date"], errors="coerce")
    data["Month"] = date_ts.dt.to_period("M").astype("string")
    data["Week"] = date_ts.dt.isocalendar().week.astype("Int64")

    def _extract_hour(value: object):
        if pd.isna(value):
            return pd.NA
        if isinstance(value, time):
            return value.hour
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return pd.NA
        return int(parsed.hour)

    data["Hour_Start"] = data["Awal"].apply(_extract_hour).astype("Int64")

    shift_num = (
        data["Shift"].astype("string").str.extract(r"(\d+)")[0]
    )
    data["Shift_Num"] = pd.to_numeric(shift_num, errors="coerce").astype("Int64")
    return data
