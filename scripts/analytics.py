from __future__ import annotations

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict[str, object]:
    total_bd = len(df)
    total_hours = pd.to_numeric(df.get("Duration_Real"), errors="coerce").sum()
    avg_duration = pd.to_numeric(df.get("Duration_Real"), errors="coerce").mean()

    top_category = (
        df.groupby("Category", dropna=False)["Duration_Real"].sum().sort_values(ascending=False).index[0]
        if total_bd
        else "-"
    )
    top_unit = (
        df.groupby("CN Unit", dropna=False)["Duration_Real"].sum().sort_values(ascending=False).index[0]
        if total_bd
        else "-"
    )

    return {
        "total_breakdown_count": int(total_bd),
        "total_downtime_hours": float(total_hours) if pd.notna(total_hours) else 0.0,
        "average_repair_duration": float(avg_duration) if pd.notna(avg_duration) else 0.0,
        "top_breakdown_category": str(top_category),
        "top_problematic_unit": str(top_unit),
    }

