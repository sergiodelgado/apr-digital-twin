from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Any

import pandas as pd
import requests
import streamlit as st

from apr_twin.config import (
    FRESHNESS_FRESH_MAX_MINUTES,
    FRESHNESS_STALE_MAX_MINUTES,
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
st.title("APR Operational Control Room")

FILTER_SOURCE_OPTIONS = ["Local Parquet", "API"]
DEFAULT_API_URL = "http://127.0.0.1:8000"
MAX_INCIDENT_ROWS = 120
MAX_RAW_TELEMETRY_ROWS = 120


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


def _coerce_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _resolve_bounds_for_apr(date_bounds: dict[str, tuple[date, date]], apr_id: str) -> tuple[date, date] | None:
    if apr_id in date_bounds:
        return date_bounds[apr_id]
    if not date_bounds:
        return None
    min_date = min(bounds[0] for bounds in date_bounds.values())
    max_date = max(bounds[1] for bounds in date_bounds.values())
    return min_date, max_date


def _clamp_date_range(
    requested_start: Any,
    requested_end: Any,
    min_date: date,
    max_date: date,
) -> tuple[date, date]:
    start_date = _coerce_date(requested_start) or min_date
    end_date = _coerce_date(requested_end) or max_date
    start_date = max(min_date, min(max_date, start_date))
    end_date = max(min_date, min(max_date, end_date))
    if start_date > end_date:
        return end_date, start_date
    return start_date, end_date


def _build_local_date_bounds(
    silver_df: pd.DataFrame,
    gold_df: pd.DataFrame,
    apr_options: list[str],
) -> dict[str, tuple[date, date]]:
    bounds: dict[str, tuple[date, date]] = {}
    for apr_id in apr_options:
        candidates: list[pd.Timestamp] = []
        if not silver_df.empty:
            apr_silver = silver_df[silver_df["apr_id"] == apr_id]
            if not apr_silver.empty:
                candidates.extend([apr_silver["timestamp"].min(), apr_silver["timestamp"].max()])
        if not gold_df.empty:
            apr_gold = gold_df[gold_df["apr_id"] == apr_id]
            if not apr_gold.empty:
                candidates.extend([apr_gold["date"].min(), apr_gold["date"].max()])
        valid_dates = [d for d in candidates if pd.notna(d)]
        if valid_dates:
            bounds[apr_id] = (min(valid_dates).date(), max(valid_dates).date())
    return bounds


def _build_api_date_bounds(apr_catalog: list[dict[str, Any]]) -> dict[str, tuple[date, date]]:
    bounds: dict[str, tuple[date, date]] = {}
    for row in apr_catalog:
        apr_id = str(row.get("apr_id", "")).strip()
        if not apr_id:
            continue
        first_ts = pd.to_datetime(row.get("first_telemetry_timestamp"), errors="coerce")
        last_ts = pd.to_datetime(row.get("last_telemetry_timestamp"), errors="coerce")
        first_kpi = pd.to_datetime(row.get("first_kpi_date"), errors="coerce")
        last_kpi = pd.to_datetime(row.get("last_kpi_date"), errors="coerce")
        candidates = [first_ts, last_ts, first_kpi, last_kpi]
        valid_dates = [d for d in candidates if pd.notna(d)]
        if valid_dates:
            bounds[apr_id] = (min(valid_dates).date(), max(valid_dates).date())
    return bounds


def _normalize_api_url(value: str) -> str:
    url = str(value or DEFAULT_API_URL).strip()
    if not url:
        return DEFAULT_API_URL
    return url.rstrip("/")


def _format_timestamp(value: Any) -> str:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return "N/A"
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _format_minutes(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f} min"


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not pd.isna(value)


def _estimate_sampling_minutes(silver_df: pd.DataFrame) -> float | None:
    if silver_df.empty or len(silver_df) < 2:
        return None
    diffs = silver_df.sort_values("timestamp")["timestamp"].diff().dropna().dt.total_seconds() / 60.0
    if diffs.empty:
        return None
    return float(diffs.median())


def _count_event_starts(condition: pd.Series) -> int:
    if condition.empty:
        return 0
    cond = condition.fillna(False).astype(bool)
    starts = cond & ~cond.shift(fill_value=False)
    return int(starts.sum())


def _classify_severity(any_warning: bool, any_critical: bool) -> str:
    if any_critical:
        return "CRITICAL"
    if any_warning:
        return "WARNING"
    return "OK"


def _sum_gold_duration(gold_df: pd.DataFrame, col_name: str) -> float | None:
    if gold_df.empty or col_name not in gold_df.columns:
        return None
    series = pd.to_numeric(gold_df[col_name], errors="coerce").dropna()
    if series.empty:
        return None
    return float(series.sum())


def _choose_resample_rule(start_date: date, end_date: date) -> str | None:
    window_hours = max((datetime.combine(end_date, time.max) - datetime.combine(start_date, time.min)).total_seconds() / 3600.0, 0.0)
    if window_hours <= 6:
        return None
    if window_hours <= 24:
        return "2min"
    if window_hours <= 72:
        return "5min"
    if window_hours <= 7 * 24:
        return "15min"
    if window_hours <= 30 * 24:
        return "1h"
    return "3h"


@st.cache_data(ttl=20)
def _prepare_telemetry_for_dashboard(silver_df: pd.DataFrame) -> pd.DataFrame:
    if silver_df.empty:
        return silver_df
    telemetry = silver_df.copy()
    telemetry["timestamp"] = pd.to_datetime(telemetry["timestamp"], errors="coerce")
    telemetry = telemetry.dropna(subset=["timestamp"]).sort_values("timestamp")
    for col in ("pressure_bar", "tank_level_pct", "turbidity_ntu"):
        if col in telemetry.columns:
            telemetry[col] = pd.to_numeric(telemetry[col], errors="coerce")
    return telemetry


@st.cache_data(ttl=20)
def _build_chart_telemetry(
    telemetry_df: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, str]:
    if telemetry_df.empty:
        return pd.DataFrame(), "raw"

    cols = [col for col in ("pressure_bar", "tank_level_pct", "turbidity_ntu") if col in telemetry_df.columns]
    if not cols:
        return pd.DataFrame(), "raw"

    indexed = telemetry_df.set_index("timestamp")[cols].sort_index()
    rule = _choose_resample_rule(start_date, end_date)
    if rule is None:
        return indexed, "raw"

    resampled = indexed.resample(rule).mean().dropna(how="all")
    return resampled, rule


def _build_alert_summaries(
    silver_df: pd.DataFrame,
    gold_df: pd.DataFrame,
    pressure_value: float | None,
    tank_value: float | None,
    turbidity_value: float | None,
    freshness: str,
    data_age: float | None,
) -> list[dict[str, str]]:
    sampling_minutes = _estimate_sampling_minutes(silver_df)

    if silver_df.empty:
        pressure_cond = pd.Series(dtype=bool)
        pressure_critical_cond = pd.Series(dtype=bool)
        tank_cond = pd.Series(dtype=bool)
        tank_critical_cond = pd.Series(dtype=bool)
        turbidity_cond = pd.Series(dtype=bool)
        turbidity_critical_cond = pd.Series(dtype=bool)
        gaps_minutes = pd.Series(dtype=float)
    else:
        pressure_cond = silver_df["pressure_bar"] < PRESSURE_MIN_BAR
        pressure_critical_cond = silver_df["pressure_bar"] < 1.0
        tank_cond = silver_df["tank_level_pct"] < TANK_LOW_PCT
        tank_critical_cond = silver_df["tank_level_pct"] <= TANK_CRITICAL_PCT
        turbidity_cond = silver_df["turbidity_ntu"] > TURBIDITY_ALERT_NTU
        turbidity_critical_cond = silver_df["turbidity_ntu"] >= TURBIDITY_CRITICAL_NTU
        gaps_minutes = (
            silver_df.sort_values("timestamp")["timestamp"].diff().dropna().dt.total_seconds() / 60.0
        )

    pressure_duration = _sum_gold_duration(gold_df, "low_pressure_duration_minutes")
    if pressure_duration is None and sampling_minutes is not None:
        pressure_duration = float(pressure_cond.sum()) * sampling_minutes

    turbidity_duration = _sum_gold_duration(gold_df, "high_turbidity_duration_minutes")
    if turbidity_duration is None and sampling_minutes is not None:
        turbidity_duration = float(turbidity_cond.sum()) * sampling_minutes

    tank_duration: float | None = None
    if sampling_minutes is not None:
        tank_duration = float(tank_cond.sum()) * sampling_minutes

    freshness_event_count = int((gaps_minutes > FRESHNESS_FRESH_MAX_MINUTES).sum()) if not gaps_minutes.empty else 0
    freshness_critical_seen = bool((gaps_minutes > FRESHNESS_STALE_MAX_MINUTES).any()) if not gaps_minutes.empty else False
    freshness_warning_seen = bool((gaps_minutes > FRESHNESS_FRESH_MAX_MINUTES).any()) if not gaps_minutes.empty else False

    pressure_summary = {
        "title": "Pressure Stability",
        "active_now": "ACTIVE" if _is_number(pressure_value) and pressure_value < PRESSURE_MIN_BAR else "CLEAR",
        "events": str(_count_event_starts(pressure_cond)),
        "max_severity": _classify_severity(bool(pressure_cond.any()), bool(pressure_critical_cond.any())),
        "duration": _format_minutes(pressure_duration),
    }
    tank_summary = {
        "title": "Tank Level",
        "active_now": "ACTIVE" if _is_number(tank_value) and tank_value < TANK_LOW_PCT else "CLEAR",
        "events": str(_count_event_starts(tank_cond)),
        "max_severity": _classify_severity(bool(tank_cond.any()), bool(tank_critical_cond.any())),
        "duration": _format_minutes(tank_duration),
    }
    turbidity_summary = {
        "title": "Water Quality",
        "active_now": "ACTIVE" if _is_number(turbidity_value) and turbidity_value > TURBIDITY_ALERT_NTU else "CLEAR",
        "events": str(_count_event_starts(turbidity_cond)),
        "max_severity": _classify_severity(bool(turbidity_cond.any()), bool(turbidity_critical_cond.any())),
        "duration": _format_minutes(turbidity_duration),
    }

    freshness_peak_gap = float(gaps_minutes.max()) if not gaps_minutes.empty else None
    freshness_duration_text = (
        f"Current age {_format_minutes(float(data_age) if _is_number(data_age) else None)}"
        if freshness in {"STALE", "OUTDATED"}
        else _format_minutes(freshness_peak_gap)
    )
    freshness_summary = {
        "title": "Telemetry Freshness",
        "active_now": "ACTIVE" if freshness in {"STALE", "OUTDATED"} else "CLEAR",
        "events": str(freshness_event_count),
        "max_severity": _classify_severity(freshness_warning_seen, freshness_critical_seen),
        "duration": freshness_duration_text,
    }

    return [pressure_summary, tank_summary, turbidity_summary, freshness_summary]


def _render_alert_card(container: Any, summary: dict[str, str]) -> None:
    with container:
        with st.container(border=True):
            st.markdown(f"**{summary['title']}**")
            st.markdown(f"Active alert now: **{summary['active_now']}**")
            st.markdown(f"Events in selected range: **{summary['events']}**")
            st.markdown(f"Maximum severity observed: **{summary['max_severity']}**")
            st.markdown(f"Duration: **{summary['duration']}**")


def _build_operational_recommendation(
    twin: dict[str, Any],
    alert_summaries: list[dict[str, str]],
) -> dict[str, str]:
    confidence_raw = twin.get("confidence_score", twin.get("confidence", 0.0))
    confidence = float(confidence_raw) if _is_number(confidence_raw) else 0.0

    # Keep dashboard narrative anchored to the same recommendation generated by the twin engine and API.
    recommendation_text = str(twin.get("operational_recommendation") or "").strip()
    reason_codes_raw = twin.get("reason_codes", [])
    reason_codes = [str(code).strip() for code in reason_codes_raw if str(code).strip()]
    if reason_codes:
        reason_text = "Twin reason codes: " + ", ".join(reason_codes[:5])
    else:
        reason_text = "Twin engine reports no active reason codes."

    if recommendation_text:
        return {
            "recommendation": recommendation_text,
            "reason": reason_text,
            "confidence": f"{confidence * 100:.1f}%",
        }

    status = str(twin.get("system_status", "NO_DATA"))
    if status == "CRITICAL":
        fallback = "Escalate to incident response and prioritize stabilization actions at the selected APR."
    elif status == "WARNING":
        fallback = "Increase monitoring frequency and prepare corrective action if conditions persist."
    else:
        fallback = "Continue normal operation with routine surveillance and threshold tracking."
    return {
        "recommendation": fallback,
        "reason": reason_text,
        "confidence": f"{confidence * 100:.1f}%",
    }


def _latest_kpi_row(gold_df: pd.DataFrame) -> pd.Series | None:
    if gold_df.empty:
        return None
    return gold_df.sort_values("date").iloc[-1]


def _as_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def _safe_float_from_row(row: pd.Series | None, col: str) -> float | None:
    if row is None or col not in row.index:
        return None
    value = pd.to_numeric(pd.Series([row[col]]), errors="coerce").iloc[0]
    if pd.isna(value):
        return None
    return float(value)


def _build_executive_summary(
    silver_df: pd.DataFrame,
    gold_df: pd.DataFrame,
    twin: dict[str, Any],
) -> list[dict[str, str]]:
    latest_kpi = _latest_kpi_row(gold_df)

    pressure_ratio = twin.get("pressure_compliance_ratio")
    pressure_ratio = float(pressure_ratio) if _is_number(pressure_ratio) else _safe_float_from_row(latest_kpi, "pressure_ok_ratio")
    if pressure_ratio is None and not silver_df.empty:
        pressure_ratio = float(((silver_df["pressure_bar"] >= PRESSURE_MIN_BAR) & (silver_df["pressure_bar"] <= PRESSURE_MAX_BAR)).mean())
    if pressure_ratio is None:
        pressure_state = "No data"
    elif pressure_ratio >= 0.95:
        pressure_state = "On target"
    elif pressure_ratio >= 0.90:
        pressure_state = "Watch"
    else:
        pressure_state = "At risk"

    if not silver_df.empty:
        min_tank_value = pd.to_numeric(silver_df["tank_level_pct"], errors="coerce").min()
        max_turbidity_value = pd.to_numeric(silver_df["turbidity_ntu"], errors="coerce").max()
        min_tank = float(min_tank_value) if pd.notna(min_tank_value) else None
        max_turbidity = float(max_turbidity_value) if pd.notna(max_turbidity_value) else None
    else:
        min_tank = None
        max_turbidity = None

    if min_tank is None:
        tank_risk = "No data"
    elif min_tank <= TANK_CRITICAL_PCT:
        tank_risk = "High"
    elif min_tank <= TANK_LOW_PCT:
        tank_risk = "Medium"
    else:
        tank_risk = "Low"

    if max_turbidity is None:
        water_risk = "No data"
    elif max_turbidity >= TURBIDITY_CRITICAL_NTU:
        water_risk = "High"
    elif max_turbidity > TURBIDITY_ALERT_NTU:
        water_risk = "Medium"
    else:
        water_risk = "Low"

    completeness = _safe_float_from_row(latest_kpi, "completeness_pct")
    imputed = _safe_float_from_row(latest_kpi, "imputed_pct")
    if completeness is None:
        data_completeness = "No KPI in window"
        completeness_value = "N/A"
    else:
        completeness_value = f"{completeness:.1f}%"
        if completeness >= 95.0 and (imputed is None or imputed <= 5.0):
            data_completeness = "Reliable"
        elif completeness >= 90.0:
            data_completeness = "Watch"
        else:
            data_completeness = "At risk"

    imputed_text = f" | Imputed {imputed:.1f}%" if imputed is not None else ""
    return [
        {
            "label": "Pressure Compliance",
            "value": _as_percent(pressure_ratio),
            "detail": pressure_state,
        },
        {
            "label": "Tank Risk",
            "value": tank_risk,
            "detail": f"Min level {min_tank:.1f}%" if min_tank is not None else "No telemetry in window",
        },
        {
            "label": "Water Quality Risk",
            "value": water_risk,
            "detail": f"Peak turbidity {max_turbidity:.2f} NTU" if max_turbidity is not None else "No telemetry in window",
        },
        {
            "label": "Data Completeness",
            "value": completeness_value,
            "detail": f"{data_completeness}{imputed_text}",
        },
    ]


@st.cache_data(ttl=20)
def _build_incident_table(silver_df: pd.DataFrame, max_rows: int = MAX_INCIDENT_ROWS) -> pd.DataFrame:
    if silver_df.empty:
        return pd.DataFrame()
    required_cols = {"timestamp", "pressure_bar", "tank_level_pct", "turbidity_ntu"}
    if not required_cols.issubset(set(silver_df.columns)):
        return pd.DataFrame()

    incidents: list[pd.DataFrame] = []
    frame = silver_df[["timestamp", "pressure_bar", "tank_level_pct", "turbidity_ntu"]].copy()

    pressure_mask = frame["pressure_bar"] < PRESSURE_MIN_BAR
    if pressure_mask.any():
        pressure_rows = frame.loc[pressure_mask, ["timestamp", "pressure_bar"]].copy()
        pressure_rows["event"] = "Low pressure"
        pressure_rows["severity"] = "WARNING"
        pressure_rows.loc[pressure_rows["pressure_bar"] < 1.0, "severity"] = "CRITICAL"
        pressure_rows["observed_value"] = pressure_rows["pressure_bar"].map("{:.2f} bar".format)
        pressure_rows["threshold"] = f"< {PRESSURE_MIN_BAR:.2f} bar"
        incidents.append(pressure_rows.drop(columns=["pressure_bar"]))

    tank_mask = frame["tank_level_pct"] < TANK_LOW_PCT
    if tank_mask.any():
        tank_rows = frame.loc[tank_mask, ["timestamp", "tank_level_pct"]].copy()
        tank_rows["event"] = "Low tank level"
        tank_rows["severity"] = "WARNING"
        tank_rows.loc[tank_rows["tank_level_pct"] <= TANK_CRITICAL_PCT, "severity"] = "CRITICAL"
        tank_rows["observed_value"] = tank_rows["tank_level_pct"].map("{:.1f}%".format)
        tank_rows["threshold"] = f"< {TANK_LOW_PCT:.1f}%"
        incidents.append(tank_rows.drop(columns=["tank_level_pct"]))

    turbidity_mask = frame["turbidity_ntu"] > TURBIDITY_ALERT_NTU
    if turbidity_mask.any():
        turbidity_rows = frame.loc[turbidity_mask, ["timestamp", "turbidity_ntu"]].copy()
        turbidity_rows["event"] = "High turbidity"
        turbidity_rows["severity"] = "WARNING"
        turbidity_rows.loc[turbidity_rows["turbidity_ntu"] >= TURBIDITY_CRITICAL_NTU, "severity"] = "CRITICAL"
        turbidity_rows["observed_value"] = turbidity_rows["turbidity_ntu"].map("{:.2f} NTU".format)
        turbidity_rows["threshold"] = f"> {TURBIDITY_ALERT_NTU:.2f} NTU"
        incidents.append(turbidity_rows.drop(columns=["turbidity_ntu"]))

    if not incidents:
        return pd.DataFrame()

    incidents_df = pd.concat(incidents, ignore_index=True)
    incidents_df["severity_rank"] = incidents_df["severity"].map({"CRITICAL": 0, "WARNING": 1}).fillna(2)
    incidents_df = incidents_df.sort_values(["severity_rank", "timestamp"], ascending=[True, False]).head(max_rows)
    incidents_df["timestamp"] = incidents_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return incidents_df.drop(columns=["severity_rank"])


@st.cache_data(ttl=20)
def load_local_base_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = ensure_data_dirs()
    silver_df = read_parquet_file(cfg.silver_file)
    gold_df = read_parquet_file(cfg.gold_daily_file)
    return _normalize_silver(silver_df), _normalize_gold(gold_df)


@st.cache_data(ttl=20)
def load_local_filter_context() -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, tuple[date, date]]]:
    silver_df, gold_df = load_local_base_data()
    apr_options = _extract_apr_ids(silver_df, gold_df)
    date_bounds = _build_local_date_bounds(silver_df, gold_df, apr_options)
    return silver_df, gold_df, apr_options, date_bounds


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
def load_api_filter_context(base_url: str) -> tuple[list[dict[str, Any]], list[str], dict[str, tuple[date, date]]]:
    apr_catalog = load_api_aprs(base_url)
    apr_options = sorted({str(row.get("apr_id", "")).strip() for row in apr_catalog if row.get("apr_id")})
    date_bounds = _build_api_date_bounds(apr_catalog)
    return apr_catalog, apr_options, date_bounds


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


@st.cache_data(ttl=15)
def load_local_twin_state(apr_id: str) -> dict[str, Any]:
    return compute_current_state(apr_id=apr_id).model_dump()


default_filters: dict[str, Any] = {
    "data_source": FILTER_SOURCE_OPTIONS[0],
    "api_url": DEFAULT_API_URL,
    "apr_id": None,
    "start_date": None,
    "end_date": None,
}
if "applied_filters" not in st.session_state:
    st.session_state.applied_filters = default_filters.copy()

saved_filters = dict(default_filters)
saved_filters.update(dict(st.session_state.applied_filters))
applied_data_source = str(saved_filters.get("data_source"))
if applied_data_source not in FILTER_SOURCE_OPTIONS:
    applied_data_source = FILTER_SOURCE_OPTIONS[0]
applied_api_url = _normalize_api_url(str(saved_filters.get("api_url", DEFAULT_API_URL)))

silver_base = pd.DataFrame()
gold_base = pd.DataFrame()
if applied_data_source == "Local Parquet":
    silver_base, gold_base, apr_options, date_bounds = load_local_filter_context()
else:
    try:
        _, apr_options, date_bounds = load_api_filter_context(applied_api_url)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load available APRs from API: {exc}")
        st.stop()

if not apr_options:
    st.warning("No APR data found. Run `python scripts/run_mvp.py` first.")
    st.stop()

applied_apr = str(saved_filters.get("apr_id") or apr_options[0])
if applied_apr not in apr_options:
    applied_apr = apr_options[0]

applied_bounds = _resolve_bounds_for_apr(date_bounds, applied_apr)
if applied_bounds is None:
    st.warning(f"No date coverage found for APR {applied_apr}.")
    st.stop()
min_date, max_date = applied_bounds
applied_start_date, applied_end_date = _clamp_date_range(
    requested_start=saved_filters.get("start_date"),
    requested_end=saved_filters.get("end_date"),
    min_date=min_date,
    max_date=max_date,
)
global_bounds = _resolve_bounds_for_apr(date_bounds, "__all__")
form_min_date, form_max_date = global_bounds if global_bounds is not None else (min_date, max_date)

with st.sidebar.form("filters_form", clear_on_submit=False):
    form_data_source = st.radio(
        "Data access mode",
        options=FILTER_SOURCE_OPTIONS,
        index=FILTER_SOURCE_OPTIONS.index(applied_data_source),
    )
    form_api_url = st.text_input("API endpoint", value=applied_api_url)
    form_apr = st.selectbox("APR in operation", options=apr_options, index=apr_options.index(applied_apr))
    form_range = st.date_input(
        "Operational time window",
        value=(applied_start_date, applied_end_date),
        min_value=form_min_date,
        max_value=form_max_date,
    )
    apply_filters = st.form_submit_button("Apply", type="primary")

if apply_filters:
    next_data_source = str(form_data_source)
    if next_data_source not in FILTER_SOURCE_OPTIONS:
        next_data_source = FILTER_SOURCE_OPTIONS[0]
    next_api_url = _normalize_api_url(form_api_url)

    if next_data_source == "Local Parquet":
        _, _, next_apr_options, next_date_bounds = load_local_filter_context()
    else:
        try:
            _, next_apr_options, next_date_bounds = load_api_filter_context(next_api_url)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to load available APRs from API: {exc}")
            st.stop()

    if not next_apr_options:
        st.warning("No APR data found for the selected source.")
        st.stop()

    next_apr = str(form_apr or next_apr_options[0])
    if next_apr not in next_apr_options:
        next_apr = next_apr_options[0]

    next_bounds = _resolve_bounds_for_apr(next_date_bounds, next_apr)
    if next_bounds is None:
        st.warning(f"No date coverage found for APR {next_apr}.")
        st.stop()
    next_min_date, next_max_date = next_bounds
    next_start_raw, next_end_raw = _resolve_date_range(next_min_date, next_max_date, form_range)
    next_start_date, next_end_date = _clamp_date_range(
        requested_start=next_start_raw,
        requested_end=next_end_raw,
        min_date=next_min_date,
        max_date=next_max_date,
    )

    st.session_state.applied_filters = {
        "data_source": next_data_source,
        "api_url": next_api_url,
        "apr_id": next_apr,
        "start_date": next_start_date,
        "end_date": next_end_date,
    }
    st.rerun()

data_source = applied_data_source
api_url = applied_api_url
selected_apr = applied_apr
start_date = applied_start_date
end_date = applied_end_date

st.session_state.applied_filters = {
    "data_source": data_source,
    "api_url": api_url,
    "apr_id": selected_apr,
    "start_date": start_date,
    "end_date": end_date,
}

if data_source == "Local Parquet":
    silver, gold = _apply_local_filters(
        silver_df=silver_base,
        gold_df=gold_base,
        apr_id=selected_apr,
        start_date=start_date,
        end_date=end_date,
    )
    twin = load_local_twin_state(apr_id=selected_apr)
else:
    try:
        silver, gold, twin = load_api_data(api_url, selected_apr, start_date, end_date)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load API data: {exc}")
        st.stop()

if silver.empty and gold.empty:
    st.warning("No data found for the selected APR and date range.")
    st.stop()

telemetry = _prepare_telemetry_for_dashboard(silver)

status = str(twin.get("system_status", "NO_DATA"))
freshness = str(twin.get("freshness_status", "NO_DATA"))
data_age = twin.get("data_age_minutes")
last_telemetry = _format_timestamp(twin.get("timestamp"))

st.subheader("Operational Snapshot")
header_col_1, header_col_2, header_col_3, header_col_4 = st.columns(4)
header_col_1.metric("Operational status", status)

freshness_caption = f"{data_age:.1f} minutes old" if _is_number(data_age) else "Age unavailable"
badge_color = {
    "FRESH": "#15803d",
    "STALE": "#b45309",
    "OUTDATED": "#b91c1c",
    "NO_DATA": "#475569",
}.get(freshness, "#475569")
header_col_2.markdown(
    (
        "<div style='padding:0.25rem 0.5rem;border-radius:0.5rem;"
        f"background:{badge_color};color:white;font-weight:600;display:inline-block'>{freshness}</div>"
    ),
    unsafe_allow_html=True,
)
header_col_2.caption(f"Data freshness: {freshness_caption}")
header_col_3.metric("Last telemetry timestamp", last_telemetry)
header_col_4.metric("Selected APR", selected_apr)

pressure_value = twin.get("current_pressure_bar")
tank_value = twin.get("current_tank_level_pct")
turbidity_value = twin.get("current_turbidity_ntu")

alert_summaries = _build_alert_summaries(
    silver_df=telemetry,
    gold_df=gold,
    pressure_value=float(pressure_value) if _is_number(pressure_value) else None,
    tank_value=float(tank_value) if _is_number(tank_value) else None,
    turbidity_value=float(turbidity_value) if _is_number(turbidity_value) else None,
    freshness=freshness,
    data_age=float(data_age) if _is_number(data_age) else None,
)

recommendation = _build_operational_recommendation(twin=twin, alert_summaries=alert_summaries)
st.subheader("Operational Recommendation")
with st.container(border=True):
    st.markdown(f"**Recommendation:** {recommendation['recommendation']}")
    st.markdown(f"**Reason:** {recommendation['reason']}")
    st.markdown(f"**Confidence:** {recommendation['confidence']}")

st.subheader("Alert Situation Overview")
alert_cols = st.columns(4)
for col, summary in zip(alert_cols, alert_summaries):
    _render_alert_card(col, summary)

alerts = twin.get("active_alerts", [])
if alerts:
    st.warning("Current alert feed: " + " | ".join(alerts[:4]))
else:
    st.success("Current alert feed: no active alerts.")

st.subheader("Executive Summary")
summary_metrics = _build_executive_summary(silver_df=telemetry, gold_df=gold, twin=twin)
summary_cols = st.columns(4)
for col, metric in zip(summary_cols, summary_metrics):
    col.metric(metric["label"], metric["value"], metric["detail"], delta_color="inverse")

with st.expander("Daily KPI detail (technical)", expanded=False):
    if gold.empty:
        st.info("No daily KPI data found for selected filters.")
    else:
        kpi_view = gold.sort_values("date", ascending=False).head(31).copy()
        kpi_view["date"] = kpi_view["date"].dt.date
        st.dataframe(kpi_view, use_container_width=True)

st.subheader("Pressure Trend")
chart_df, chart_resolution = _build_chart_telemetry(telemetry, start_date=start_date, end_date=end_date)
if chart_df.empty or "pressure_bar" not in chart_df.columns:
    st.info("No telemetry rows available for pressure trend.")
else:
    pressure_df = chart_df[["pressure_bar"]].copy()
    pressure_df["pressure_min_threshold"] = PRESSURE_MIN_BAR
    pressure_df["pressure_max_threshold"] = PRESSURE_MAX_BAR
    st.line_chart(pressure_df)
    if chart_resolution != "raw":
        st.caption(f"Trend resolution: {chart_resolution} averages for performance.")

st.subheader("Tank Level Trend")
if chart_df.empty or "tank_level_pct" not in chart_df.columns:
    st.info("No telemetry rows available for tank trend.")
else:
    tank_df = chart_df[["tank_level_pct"]].copy()
    tank_df["tank_low_threshold"] = TANK_LOW_PCT
    tank_df["tank_critical_threshold"] = TANK_CRITICAL_PCT
    st.line_chart(tank_df)

st.subheader("Turbidity Trend")
if chart_df.empty or "turbidity_ntu" not in chart_df.columns:
    st.info("No telemetry rows available for turbidity trend.")
else:
    turbidity_df = chart_df[["turbidity_ntu"]].copy()
    turbidity_df["turbidity_alert_threshold"] = TURBIDITY_ALERT_NTU
    turbidity_df["turbidity_critical_threshold"] = TURBIDITY_CRITICAL_NTU
    st.line_chart(turbidity_df)

st.subheader("Incidents and Events")
incidents_df = _build_incident_table(telemetry, max_rows=MAX_INCIDENT_ROWS)
if incidents_df.empty:
    st.success("No incidents detected in the selected time window.")
else:
    st.dataframe(incidents_df, use_container_width=True)

with st.expander("Raw telemetry (secondary view)", expanded=False):
    if silver.empty:
        st.info("No telemetry available for the selected filters.")
    else:
        raw_cols = [
            "timestamp",
            "apr_id",
            "sensor_id",
            "flow_lps",
            "pressure_bar",
            "tank_level_pct",
            "turbidity_ntu",
            "pump_on",
            "pressure_ok",
            "turbidity_alert",
            "is_imputed",
            "batch_id",
        ]
        available_cols = [col for col in raw_cols if col in telemetry.columns]
        raw_view = telemetry[available_cols].sort_values("timestamp", ascending=False).head(MAX_RAW_TELEMETRY_ROWS).copy()
        st.dataframe(raw_view, use_container_width=True)
