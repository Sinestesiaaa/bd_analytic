from __future__ import annotations

import pandas as pd
import plotly.express as px


def chart_pareto_category(df: pd.DataFrame):
    agg = (
        df.groupby("Category", dropna=False)["Duration_Real"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    return px.bar(agg, x="Category", y="Duration_Real", title="Pareto Breakdown by Category")


def chart_daily_trend(df: pd.DataFrame):
    agg = df.groupby("Date", dropna=False)["Duration_Real"].sum().reset_index()
    return px.line(agg, x="Date", y="Duration_Real", title="Daily Downtime Trend")


def chart_top_units(df: pd.DataFrame, top_n: int = 10):
    agg = (
        df.groupby("CN Unit", dropna=False)["Duration_Real"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    return px.bar(agg, x="CN Unit", y="Duration_Real", title=f"Top {top_n} Problematic Units")


def chart_by_location(df: pd.DataFrame):
    agg = df.groupby("Location", dropna=False)["Duration_Real"].sum().reset_index()
    return px.bar(agg, x="Location", y="Duration_Real", title="Breakdown by Location")


def chart_heatmap(df: pd.DataFrame):
    heat = (
        df.groupby(["Hour_Start", "Date"], dropna=False)["Duration_Real"]
        .sum()
        .reset_index(name="Total_Duration")
    )
    return px.density_heatmap(
        heat,
        x="Date",
        y="Hour_Start",
        z="Total_Duration",
        title="Breakdown Heatmap (Hour vs Date)",
    )


def chart_timeline(df: pd.DataFrame):
    timeline = df.copy()
    timeline["Start"] = pd.to_datetime(
        timeline["Date"].astype("string") + " " + timeline["Awal"].astype("string"), errors="coerce"
    )
    timeline["End"] = timeline["Start"] + pd.to_timedelta(
        pd.to_numeric(timeline["Duration_Real"], errors="coerce"), unit="h"
    )
    timeline = timeline.dropna(subset=["Start", "End"])
    return px.timeline(
        timeline,
        x_start="Start",
        x_end="End",
        y="CN Unit",
        color="Subcategory",
        title="Breakdown Timeline by Subcategory",
    )
