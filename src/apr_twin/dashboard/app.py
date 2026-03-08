from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Any

import pandas as pd
import requests
import streamlit as st

from apr_twin.config import (
    PRESSURE_MAX_BAR,
    PRESSURE_MIN_BAR,
    TANK_CRITICAL_PCT,
    TANK_LOW_PCT,
    TURBIDITY_ALERT_NTU,
    TURBIDITY_CRITICAL_NTU,
    ensure_data_dirs,
)
from apr_twin.storage.parquet_io import read_parquet_file
from apr_twin.twin.engine import compute_current_state
from apr_twin.utils.logging_utils import configure_logging

configure_logging()
LOGGER = logging.getLogger(__name__)

st.set_page_config(page_title="APR Digital Twin", layout="wide")
st.title("APR Digital Twin MVP")


def _normalize_silver(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out = out.dropna(subset=["timestamp"]).sort_values("timestamp")
    return out


def _normalize_gold(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    return out


def _extract_apr_ids(silver_df: pd.DataFrame, gold_df: pd.DataFrame) -> list[str]:
    apr_ids: set[str] = set()
    if not silver_df.empty:
        apr_ids.update(silver_df["apr_id"].dropna().astype(str).str.strip())
    if not gold_df.empty:
        apr_ids.update(gold_df["apr_id"].dropna().astype(str).str.strip())
    apr_ids.discard("")
    return sorted(apr_ids)


def _resolve_date_range(min_date: date, max_date: date, value: Any) -> tuple[date, date]:
    if isinstance(value, tuple) and len(value) == 2:
        start_date = value[0]
        end_date = value[1]
    elif isinstance(value, list) and len(value) == 2:
        start_date = value[0]
        end_date = value[1]
    elif isinstance(value, date):
        start_date = value
        end_date = value
    else:
        start_date = min_date
        end_date = max_date
    if start_date > end_date:
        return end_date, start_date
    return start_date, end_date


def _apply_local_filters(
    silver_df: pd.DataFrame,
    gold_df: pd.DataFrame,
    apr_id: str | None,
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = silver_df.copy()
    g = gold_df.copy()

    if apr_id:
        if not s.empty:
            s = s[s["apr_id"] == apr_id]
        if not g.empty:
            g = g[g["apr_id"] == apr_id]

    start_ts = pd.Timestamp(datetime.combine(start_date, time.min))
    end_ts = pd.Timestamp(datetime.combine(end_date, time.max))
    if not s.empty:
        s = s[(s["timestamp"] >= start_ts) & (s["timestamp"] <= end_ts)]
    if not g.empty:
        g = g[(g["date"] >= start_ts.floor("D")) & (g["date"] <= end_ts.floor("D"))]

    return s, g


@st.cache_data(ttl=20)
def load_local_base_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = ensure_data_dirs()
    silver_df = read_parquet_file(cfg.silver_file)
    gold_df = read_parquet_file(cfg.gold_daily_file)
    return _normalize_silver(silver_df), _normalize_gold(gold_df)


@st.cache_data(ttl=15)
def load_api_aprs(base_url: str) -> list[dict[str, Any]]:
    last_exception: Exception | None = None
    for path in ("/available_aprs", "/aprs/available"):
        try:
            response = requests.get(f"{base_url}{path}", timeout=20)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                return []
            return [row for row in payload if isinstance(row, dict)]
        except Exception as exc:  # noqa: BLE001
            last_exception = exc
    if last_exception is not None:
        raise last_exception
    return []


@st.cache_data(ttl=15)
def load_api_data(
    base_url: str,
    apr_id: str | None,
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    telemetry_params: dict[str, Any] = {
        "limit": 5000,
        "start": datetime.combine(start_date, time.min).isoformat(),
        "end": datetime.combine(end_date, time.max).isoformat(),
    }
    kpi_params: dict[str, Any] = {
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
    }
    twin_params: dict[str, Any] = {}
    if apr_id:
        telemetry_params["apr_id"] = apr_id
        kpi_params["apr_id"] = apr_id
        twin_params["apr_id"] = apr_id

    telemetry_resp = requests.get(f"{base_url}/telemetry/recent", params=telemetry_params, timeout=20)
    telemetry_resp.raise_for_status()
    kpi_resp = requests.get(f"{base_url}/kpis/daily", params=kpi_params, timeout=20)
    kpi_resp.raise_for_status()
    twin_resp = requests.get(f"{base_url}/twin/state", params=twin_params, timeout=20)
    twin_resp.raise_for_status()

    silver_df = _normalize_silver(pd.DataFrame(telemetry_resp.json()))
    gold_df = _normalize_gold(pd.DataFrame(kpi_resp.json()))
    twin_state = twin_resp.json()
    return silver_df, gold_df, twin_state


data_source = st.sidebar.radio("Data source", options=["Local Parquet", "API"], index=0)
api_url = st.sidebar.text_input("API URL", value="http://127.0.0.1:8000").strip().rstrip("/")

if data_source == "Local Parquet":
    silver_base, gold_base = load_local_base_data()
    apr_options = _extract_apr_ids(silver_base, gold_base)
    apr_catalog: list[dict[str, Any]] = []
else:
    try:
        apr_catalog = load_api_aprs(api_url)
        apr_options = sorted({str(row.get("apr_id", "")).strip() for row in apr_catalog if row.get("apr_id")})
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load available APRs from API: {exc}")
        st.stop()

if not apr_options:
    st.warning("No APR data found. Run `python scripts/run_mvp.py` first.")
    st.stop()

selected_apr = st.sidebar.selectbox("APR selector", options=apr_options, index=0)

if data_source == "Local Parquet":
    apr_silver = silver_base[silver_base["apr_id"] == selected_apr] if not silver_base.empty else pd.DataFrame()
    apr_gold = gold_base[gold_base["apr_id"] == selected_apr] if not gold_base.empty else pd.DataFrame()
    date_candidates: list[pd.Timestamp] = []
    if not apr_silver.empty:
        date_candidates.extend([apr_silver["timestamp"].min(), apr_silver["timestamp"].max()])
    if not apr_gold.empty:
        date_candidates.extend([apr_gold["date"].min(), apr_gold["date"].max()])
else:
    apr_meta = next((row for row in apr_catalog if str(row.get("apr_id")) == selected_apr), {})
    first_ts = pd.to_datetime(apr_meta.get("first_telemetry_timestamp"), errors="coerce")
    last_ts = pd.to_datetime(apr_meta.get("last_telemetry_timestamp"), errors="coerce")
    first_kpi = pd.to_datetime(apr_meta.get("first_kpi_date"), errors="coerce")
    last_kpi = pd.to_datetime(apr_meta.get("last_kpi_date"), errors="coerce")
    date_candidates = [first_ts, last_ts, first_kpi, last_kpi]

valid_dates = [d for d in date_candidates if pd.notna(d)]
if not valid_dates:
    st.warning(f"No date coverage found for APR {selected_apr}.")
    st.stop()

min_date = min(valid_dates).date()
max_date = max(valid_dates).date()

range_value = st.sidebar.date_input(
    "Date range selector",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
start_date, end_date = _resolve_date_range(min_date=min_date, max_date=max_date, value=range_value)

if data_source == "Local Parquet":
    silver, gold = _apply_local_filters(
        silver_df=silver_base,
        gold_df=gold_base,
        apr_id=selected_apr,
        start_date=start_date,
        end_date=end_date,
    )
    twin = compute_current_state(apr_id=selected_apr).model_dump()
else:
    try:
        silver, gold, twin = load_api_data(api_url, selected_apr, start_date, end_date)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load API data: {exc}")
        st.stop()

if silver.empty and gold.empty:
    st.warning("No data found for the selected APR and date range.")
    st.stop()

st.subheader("Current Status")
status_col, freshness_col, pressure_col, tank_col, turbidity_col = st.columns(5)
status_col.metric("System status", str(twin.get("system_status", "NO_DATA")))

freshness = str(twin.get("freshness_status", "NO_DATA"))
data_age = twin.get("data_age_minutes")
badge_color = {
    "FRESH": "#15803d",
    "STALE": "#b45309",
    "OUTDATED": "#b91c1c",
    "NO_DATA": "#475569",
}.get(freshness, "#475569")
freshness_caption = f"{data_age:.1f} min old" if isinstance(data_age, (int, float)) else "Age unavailable"
freshness_col.markdown(
    (
        "<div style='padding:0.25rem 0.5rem;border-radius:0.5rem;"
        f"background:{badge_color};color:white;font-weight:600;display:inline-block'>{freshness}</div>"
    ),
    unsafe_allow_html=True,
)
freshness_col.caption(f"Freshness badge: {freshness_caption}")

pressure_value = twin.get("current_pressure_bar")
tank_value = twin.get("current_tank_level_pct")
turbidity_value = twin.get("current_turbidity_ntu")
pressure_col.metric("Pressure (bar)", f"{pressure_value:.2f}" if pressure_value is not None else "N/A")
tank_col.metric("Tank level (%)", f"{tank_value:.1f}" if tank_value is not None else "N/A")
turbidity_col.metric("Turbidity (NTU)", f"{turbidity_value:.2f}" if turbidity_value is not None else "N/A")

st.subheader("Top Alert Cards")
alerts = twin.get("active_alerts", [])
low_pressure_events = int((silver["pressure_bar"] < PRESSURE_MIN_BAR).sum()) if not silver.empty else 0
high_turbidity_events = int((silver["turbidity_ntu"] > TURBIDITY_ALERT_NTU).sum()) if not silver.empty else 0
low_tank_events = int((silver["tank_level_pct"] < TANK_LOW_PCT).sum()) if not silver.empty else 0

low_pressure_active = isinstance(pressure_value, (int, float)) and pressure_value < PRESSURE_MIN_BAR
high_turbidity_active = isinstance(turbidity_value, (int, float)) and turbidity_value > TURBIDITY_ALERT_NTU
low_tank_active = isinstance(tank_value, (int, float)) and tank_value < TANK_LOW_PCT
stale_data_active = freshness in {"STALE", "OUTDATED"}

stale_detail = freshness_caption
if isinstance(data_age, (int, float)):
    stale_detail = f"{freshness} ({data_age:.1f} min)"

alert_col_1, alert_col_2, alert_col_3, alert_col_4 = st.columns(4)
alert_col_1.metric(
    "Low pressure",
    "ALERT" if low_pressure_active else "OK",
    f"{low_pressure_events} events in range",
    delta_color="inverse",
)
alert_col_2.metric(
    "High turbidity",
    "ALERT" if high_turbidity_active else "OK",
    f"{high_turbidity_events} events in range",
    delta_color="inverse",
)
alert_col_3.metric(
    "Tank low",
    "ALERT" if low_tank_active else "OK",
    f"{low_tank_events} events in range",
    delta_color="inverse",
)
alert_col_4.metric(
    "Stale data",
    "ALERT" if stale_data_active else "OK",
    stale_detail,
    delta_color="inverse",
)
if alerts:
    st.warning(" | ".join(alerts[:4]))
else:
    st.success("No active alerts for selected APR.")

st.subheader("Daily KPIs")
if gold.empty:
    st.info("No daily KPI data found for selected filters.")
else:
    kpi_view = gold.sort_values("date", ascending=False).head(31).copy()
    kpi_view["date"] = kpi_view["date"].dt.date
    st.dataframe(kpi_view, use_container_width=True)

st.subheader("Pressure Trend")
if silver.empty:
    st.info("No telemetry rows available for pressure trend.")
else:
    pressure_df = silver[["timestamp", "pressure_bar"]].set_index("timestamp").copy()
    pressure_df["pressure_min_threshold"] = PRESSURE_MIN_BAR
    pressure_df["pressure_max_threshold"] = PRESSURE_MAX_BAR
    st.line_chart(pressure_df)

st.subheader("Tank Level Trend")
if silver.empty:
    st.info("No telemetry rows available for tank trend.")
else:
    tank_df = silver[["timestamp", "tank_level_pct"]].set_index("timestamp").copy()
    tank_df["tank_low_threshold"] = TANK_LOW_PCT
    tank_df["tank_critical_threshold"] = TANK_CRITICAL_PCT
    st.line_chart(tank_df)

st.subheader("Turbidity Trend")
if silver.empty:
    st.info("No telemetry rows available for turbidity trend.")
else:
    turbidity_df = silver[["timestamp", "turbidity_ntu"]].set_index("timestamp").copy()
    turbidity_df["turbidity_alert_threshold"] = TURBIDITY_ALERT_NTU
    turbidity_df["turbidity_critical_threshold"] = TURBIDITY_CRITICAL_NTU
    st.line_chart(turbidity_df)

st.subheader("Turbidity Alerts")
if silver.empty:
    alerts_df = pd.DataFrame()
elif "turbidity_alert" in silver.columns:
    alerts_df = silver[silver["turbidity_alert"] == True].copy()  # noqa: E712
else:
    alerts_df = silver[silver["turbidity_ntu"] > TURBIDITY_ALERT_NTU].copy()

if alerts_df.empty:
    st.success("No turbidity alerts in selected data.")
else:
    cols = ["timestamp", "apr_id", "turbidity_ntu", "pressure_bar", "tank_level_pct"]
    st.dataframe(alerts_df[cols].sort_values("timestamp", ascending=False).head(50), use_container_width=True)
