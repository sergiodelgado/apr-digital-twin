from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import requests
import streamlit as st

from apr_twin.config import TURBIDITY_ALERT_NTU, ensure_data_dirs
from apr_twin.storage.parquet_io import read_parquet_file
from apr_twin.twin.engine import compute_current_state
from apr_twin.utils.logging_utils import configure_logging

configure_logging()
LOGGER = logging.getLogger(__name__)

st.set_page_config(page_title="APR Digital Twin", layout="wide")
st.title("APR Digital Twin MVP")


@st.cache_data(ttl=20)
def load_local_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    cfg = ensure_data_dirs()
    silver_df = read_parquet_file(cfg.silver_file)
    gold_df = read_parquet_file(cfg.gold_daily_file)

    if not silver_df.empty:
        silver_df["timestamp"] = pd.to_datetime(silver_df["timestamp"], errors="coerce")
        silver_df = silver_df.dropna(subset=["timestamp"]).sort_values("timestamp")
    if not gold_df.empty:
        gold_df["date"] = pd.to_datetime(gold_df["date"], errors="coerce")
        gold_df = gold_df.dropna(subset=["date"]).sort_values("date")

    twin_state = compute_current_state().model_dump()
    return silver_df, gold_df, twin_state


@st.cache_data(ttl=15)
def load_api_data(base_url: str) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    telemetry_resp = requests.get(f"{base_url}/telemetry/recent", params={"limit": 2000}, timeout=20)
    telemetry_resp.raise_for_status()
    kpi_resp = requests.get(f"{base_url}/kpis/daily", params={"days": 30}, timeout=20)
    kpi_resp.raise_for_status()
    twin_resp = requests.get(f"{base_url}/twin/state", timeout=20)
    twin_resp.raise_for_status()

    silver_df = pd.DataFrame(telemetry_resp.json())
    gold_df = pd.DataFrame(kpi_resp.json())
    twin_state = twin_resp.json()

    if not silver_df.empty:
        silver_df["timestamp"] = pd.to_datetime(silver_df["timestamp"], errors="coerce")
        silver_df = silver_df.dropna(subset=["timestamp"]).sort_values("timestamp")
    if not gold_df.empty:
        gold_df["date"] = pd.to_datetime(gold_df["date"], errors="coerce")
        gold_df = gold_df.dropna(subset=["date"]).sort_values("date")

    return silver_df, gold_df, twin_state


data_source = st.sidebar.radio("Data source", options=["Local Parquet", "API"], index=0)
api_url = st.sidebar.text_input("API URL", value="http://127.0.0.1:8000").strip().rstrip("/")

if data_source == "Local Parquet":
    silver, gold, twin = load_local_data()
else:
    try:
        silver, gold, twin = load_api_data(api_url)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load API data: {exc}")
        st.stop()

if silver.empty:
    st.warning("No telemetry data found. Run `python scripts/run_mvp.py` first.")
    st.stop()

st.subheader("Current Status")
status_col, pressure_col, tank_col, turbidity_col = st.columns(4)
status_col.metric("System status", str(twin.get("system_status", "NO_DATA")))
pressure_value = twin.get("current_pressure_bar")
tank_value = twin.get("current_tank_level_pct")
turbidity_value = twin.get("current_turbidity_ntu")
pressure_col.metric("Pressure (bar)", f"{pressure_value:.2f}" if pressure_value is not None else "N/A")
tank_col.metric("Tank level (%)", f"{tank_value:.1f}" if tank_value is not None else "N/A")
turbidity_col.metric("Turbidity (NTU)", f"{turbidity_value:.2f}" if turbidity_value is not None else "N/A")

alerts = twin.get("active_alerts", [])
if alerts:
    st.warning(" | ".join(alerts))
else:
    st.success("No active alerts.")

st.subheader("Daily KPIs")
if gold.empty:
    st.info("No daily KPI data found yet.")
else:
    kpi_view = gold.sort_values("date", ascending=False).head(14).copy()
    kpi_view["date"] = kpi_view["date"].dt.date
    st.dataframe(kpi_view, use_container_width=True)

st.subheader("Pressure Trend")
pressure_df = silver[["timestamp", "pressure_bar"]].set_index("timestamp")
st.line_chart(pressure_df)

st.subheader("Tank Level Trend")
tank_df = silver[["timestamp", "tank_level_pct"]].set_index("timestamp")
st.line_chart(tank_df)

st.subheader("Turbidity Alerts")
if "turbidity_alert" in silver.columns:
    alerts_df = silver[silver["turbidity_alert"] == True].copy()  # noqa: E712
else:
    alerts_df = silver[silver["turbidity_ntu"] > TURBIDITY_ALERT_NTU].copy()

if alerts_df.empty:
    st.success("No turbidity alerts in selected data.")
else:
    cols = ["timestamp", "apr_id", "turbidity_ntu", "pressure_bar", "tank_level_pct"]
    st.dataframe(alerts_df[cols].sort_values("timestamp", ascending=False).head(50), use_container_width=True)


