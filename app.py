from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from scripts.analytics import compute_kpis
from scripts.classify import add_classification_columns
from scripts.cleaning import clean_and_transform, load_raw_data
from scripts.visualization import (
    chart_by_location,
    chart_daily_trend,
    chart_heatmap,
    chart_pareto_category,
    chart_timeline,
    chart_top_units,
)

st.set_page_config(page_title="Breakdown Analytics Dashboard", layout="wide")
st.title("Breakdown Analytics & Maintenance Dashboard")
st.caption("Interactive dashboard for heavy equipment breakdown monitoring")

data_folder = Path(__file__).parent / "data" / "raw"
df_raw = load_raw_data(data_folder)

if df_raw.empty:
    st.info("No Excel files found in data/raw. Please add files first.")
    st.stop()

df_clean = clean_and_transform(df_raw)
df = add_classification_columns(df_clean)

st.sidebar.header("Filters")
date_values = pd.to_datetime(df["Date"], errors="coerce").dropna()
if date_values.empty:
    date_min = pd.Timestamp.today().date()
    date_max = pd.Timestamp.today().date()
else:
    date_min = date_values.min().date()
    date_max = date_values.max().date()

date_range = st.sidebar.date_input("Date Range", value=(date_min, date_max))
model_opt = st.sidebar.multiselect("Model", sorted(df["Model"].dropna().astype(str).unique()))
unit_opt = st.sidebar.multiselect("Unit", sorted(df["CN Unit"].dropna().astype(str).unique()))
shift_opt = st.sidebar.multiselect("Shift", sorted(df["Shift"].dropna().astype(str).unique()))
loc_opt = st.sidebar.multiselect("Location", sorted(df["Location"].dropna().astype(str).unique()))
cat_opt = st.sidebar.multiselect("Category", sorted(df["Category"].dropna().astype(str).unique()))
if cat_opt:
    subcat_pool = (
        df[df["Category"].astype(str).isin(cat_opt)]["Subcategory"].dropna().astype(str).unique()
    )
else:
    subcat_pool = df["Subcategory"].dropna().astype(str).unique()
subcat_opt = st.sidebar.multiselect("Subcategory", sorted(subcat_pool))
sev_opt = st.sidebar.multiselect("Severity", sorted(df["Severity"].dropna().astype(str).unique()))
valid_opt = st.sidebar.multiselect(
    "Duration Check", sorted(df["Duration_Check"].dropna().astype(str).unique())
)
st.sidebar.markdown("### Hour Filters")
first_hours_mode = st.sidebar.checkbox("Filter N First Hours per Shift")
first_hours_n = st.sidebar.selectbox("N First Hours", options=[2, 3, 4, 6], index=0)
last_hours_mode = st.sidebar.checkbox("Filter N Last Hours per Shift")
last_hours_n = st.sidebar.selectbox("N Last Hours", options=[2, 3, 4, 6], index=0)

filtered = df.copy()
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        (pd.to_datetime(filtered["Date"], errors="coerce").dt.date >= start_date)
        & (pd.to_datetime(filtered["Date"], errors="coerce").dt.date <= end_date)
    ]
if model_opt:
    filtered = filtered[filtered["Model"].astype(str).isin(model_opt)]
if unit_opt:
    filtered = filtered[filtered["CN Unit"].astype(str).isin(unit_opt)]
if shift_opt:
    filtered = filtered[filtered["Shift"].astype(str).isin(shift_opt)]
if loc_opt:
    filtered = filtered[filtered["Location"].astype(str).isin(loc_opt)]
if cat_opt:
    filtered = filtered[filtered["Category"].astype(str).isin(cat_opt)]
if subcat_opt:
    filtered = filtered[filtered["Subcategory"].astype(str).isin(subcat_opt)]
if sev_opt:
    filtered = filtered[filtered["Severity"].astype(str).isin(sev_opt)]
if valid_opt:
    filtered = filtered[filtered["Duration_Check"].astype(str).isin(valid_opt)]

if first_hours_mode:
    shift_start_map = {
        "SHIFT 1": 6,
        "SHIFT 2": 18,
        "SHIFT 3": 0,
    }
    shift_norm = filtered["Shift"].astype("string").str.upper().str.strip()
    shift_start = shift_norm.map(shift_start_map)
    hour_start = pd.to_numeric(filtered["Hour_Start"], errors="coerce")
    hour_from_shift = (hour_start - shift_start) % 24
    filtered = filtered[hour_from_shift.between(0, first_hours_n - 1, inclusive="both")]

if last_hours_mode:
    shift_start_map = {
        "SHIFT 1": 6,
        "SHIFT 2": 18,
        "SHIFT 3": 0,
    }
    shift_norm = filtered["Shift"].astype("string").str.upper().str.strip()
    shift_start = shift_norm.map(shift_start_map)
    hour_start = pd.to_numeric(filtered["Hour_Start"], errors="coerce")
    hour_from_shift = (hour_start - shift_start) % 24
    filtered = filtered[hour_from_shift.between(12 - last_hours_n, 11, inclusive="both")]

st.sidebar.markdown("---")
st.sidebar.caption(f"Raw rows: {len(df):,}")
st.sidebar.caption(f"Filtered rows: {len(filtered):,}")

if filtered.empty:
    st.warning("No data matches current filters. Please adjust filter values.")
    st.stop()

kpi = compute_kpis(filtered)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total BD", f"{kpi['total_breakdown_count']:,}")
c2.metric("Total Hours", f"{kpi['total_downtime_hours']:.2f}")
c3.metric("Avg Repair (h)", f"{kpi['average_repair_duration']:.2f}")  # MTTR proxy
c4.metric("Top Unit", kpi["top_problematic_unit"])
c5.metric("Top Category", kpi["top_breakdown_category"])

days_covered = max(
    1,
    (
        pd.to_datetime(filtered["Date"], errors="coerce").max()
        - pd.to_datetime(filtered["Date"], errors="coerce").min()
    ).days
    + 1,
)
daily_bd_rate = len(filtered) / days_covered
mtbf_days = 1 / daily_bd_rate if daily_bd_rate > 0 else 0
availability_est = max(
    0.0, 100 - (float(kpi["total_downtime_hours"]) / (days_covered * 24) * 100)
)
c6.metric("Est. Availability", f"{availability_est:.1f}%")

st.caption(f"Estimated MTBF: {mtbf_days:.2f} days/failure across filtered range")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Pattern", "Unit Detail", "Detail"])

with tab1:
    st.plotly_chart(chart_pareto_category(filtered), use_container_width=True)
    subcat_all = (
        filtered.groupby("Subcategory", dropna=False)["Duration_Real"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_subcat_all = px.bar(
        subcat_all,
        x="Subcategory",
        y="Duration_Real",
        title="Pareto Breakdown by Subcategory",
    )
    st.plotly_chart(fig_subcat_all, use_container_width=True)

    st.markdown("### Category to Subcategory Drilldown")
    available_categories = sorted(filtered["Category"].dropna().astype(str).unique())
    drill_category = st.selectbox("Select Category", options=available_categories)
    drill_df = filtered[filtered["Category"].astype(str) == drill_category]
    drill_subcat = (
        drill_df.groupby("Subcategory", dropna=False)["Duration_Real"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_drill = px.bar(
        drill_subcat,
        x="Subcategory",
        y="Duration_Real",
        title=f"Subcategory Detail - {drill_category}",
    )
    st.plotly_chart(fig_drill, use_container_width=True)

    st.plotly_chart(chart_daily_trend(filtered), use_container_width=True)
    a, b = st.columns(2)
    with a:
        st.plotly_chart(chart_top_units(filtered), use_container_width=True)
    with b:
        st.plotly_chart(chart_by_location(filtered), use_container_width=True)

with tab2:
    st.plotly_chart(chart_heatmap(filtered), use_container_width=True)
    st.plotly_chart(chart_timeline(filtered), use_container_width=True)

with tab3:
    unit_agg = (
        filtered.groupby("CN Unit", dropna=False)
        .agg(
            Breakdown_Count=("CN Unit", "count"),
            Total_Downtime=("Duration_Real", "sum"),
            Avg_Duration=("Duration_Real", "mean"),
        )
        .reset_index()
        .sort_values(["Total_Downtime", "Breakdown_Count"], ascending=[False, False])
    )
    fig_all_units = px.bar(
        unit_agg,
        x="CN Unit",
        y="Total_Downtime",
        hover_data=["Breakdown_Count", "Avg_Duration"],
        title="All Units - Total Downtime",
    )
    st.plotly_chart(fig_all_units, use_container_width=True)
    st.dataframe(unit_agg, use_container_width=True, height=360)

    st.markdown("### Unit Problem Matrix (Category + Subcategory)")
    unit_matrix = (
        filtered.groupby(["CN Unit", "Category", "Subcategory"], dropna=False)
        .agg(Breakdown_Count=("CN Unit", "count"), Total_Downtime=("Duration_Real", "sum"))
        .reset_index()
        .sort_values(["CN Unit", "Total_Downtime"], ascending=[True, False])
    )
    st.dataframe(unit_matrix, use_container_width=True, height=420)

with tab4:
    view_cols = [
        "Date",
        "Model",
        "CN Unit",
        "Description of Breakdown",
        "Awal",
        "Akhir",
        "Category",
        "Subcategory",
        "Severity",
        "Shift",
        "Location",
        "Hours",
        "Duration_Real",
        "Duration_Check",
        "PIC Breakdown",
    ]
    available_cols = [c for c in view_cols if c in filtered.columns]
    st.dataframe(
        filtered[available_cols].sort_values(by="Date", ascending=False),
        use_container_width=True,
        height=520,
    )
    st.download_button(
        label="Download Filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="breakdown_filtered.csv",
        mime="text/csv",
    )
