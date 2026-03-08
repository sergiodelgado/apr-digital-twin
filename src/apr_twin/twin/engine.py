from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

import pandas as pd

from apr_twin.config import (
    FRESHNESS_FRESH_MAX_MINUTES,
    FRESHNESS_STALE_MAX_MINUTES,
    PRESSURE_MIN_BAR,
    TANK_CRITICAL_PCT,
    TANK_LOW_PCT,
    TURBIDITY_ALERT_NTU,
    TURBIDITY_CRITICAL_NTU,
    ensure_data_dirs,
)
from apr_twin.schemas import TwinState
from apr_twin.storage.parquet_io import read_parquet_file

LOGGER = logging.getLogger(__name__)


def _append_reason(reason_codes: list[str], code: str) -> None:
    if code and code not in reason_codes:
        reason_codes.append(code)


def _confidence_label(confidence_score: float) -> Literal["LOW", "MEDIUM", "HIGH"]:
    if confidence_score >= 0.8:
        return "HIGH"
    if confidence_score >= 0.55:
        return "MEDIUM"
    return "LOW"


def _project_tank_level_2h(apr_df: pd.DataFrame, latest_ts: pd.Timestamp, current_tank: float) -> float | None:
    recent = apr_df[apr_df["timestamp"] >= (latest_ts - pd.Timedelta(hours=2))][["timestamp", "tank_level_pct"]].copy()
    recent = recent.dropna(subset=["timestamp", "tank_level_pct"]).sort_values("timestamp")
    if len(recent) < 2:
        recent = apr_df[["timestamp", "tank_level_pct"]].dropna(subset=["timestamp", "tank_level_pct"]).sort_values("timestamp").tail(24)
    if len(recent) < 2:
        return None

    first = recent.iloc[0]
    last = recent.iloc[-1]
    first_ts = pd.Timestamp(first["timestamp"])
    last_ts = pd.Timestamp(last["timestamp"])
    minutes = float((last_ts - first_ts).total_seconds() / 60.0)
    if minutes <= 0:
        return None

    first_tank = float(first["tank_level_pct"])
    last_tank = float(last["tank_level_pct"])
    slope_per_min = (last_tank - first_tank) / minutes
    projected = current_tank + (slope_per_min * 120.0)
    projected = max(0.0, min(100.0, projected))
    return round(projected, 2)


def _classify_data_completeness(completeness_pct: float | None, imputed_pct: float | None) -> Literal["GOOD", "WATCH", "AT_RISK", "UNKNOWN"]:
    if completeness_pct is None:
        return "UNKNOWN"
    if completeness_pct < 90.0 or (imputed_pct is not None and imputed_pct > 10.0):
        return "AT_RISK"
    if completeness_pct < 95.0 or (imputed_pct is not None and imputed_pct > 5.0):
        return "WATCH"
    return "GOOD"


def _build_operational_recommendation(
    freshness_status: str,
    pressure_low: bool,
    pressure_critical: bool,
    tank_low: bool,
    tank_critical: bool,
    projected_tank_low: bool,
    projected_tank_critical: bool,
    turbidity_high: bool,
    turbidity_critical: bool,
    data_completeness_state: str,
) -> str:
    if freshness_status == "OUTDATED":
        return "Validate telemetry connectivity and operate with field confirmation until live data recovers."
    if pressure_critical:
        return "Escalate immediately for critical low pressure and stabilize distribution."
    if pressure_low:
        return "Investigate pressure losses and adjust pumping or valve operations."
    if tank_critical or projected_tank_critical:
        return "Prioritize immediate refill actions to avoid service interruption risk."
    if tank_low or projected_tank_low:
        return "Prepare short-term replenishment and monitor tank level more frequently."
    if turbidity_critical:
        return "Activate water quality incident response and verify treatment performance."
    if turbidity_high:
        return "Increase water quality surveillance and inspect treatment conditions."
    if data_completeness_state == "AT_RISK":
        return "Validate sensor data quality before relying on automated operational decisions."
    if data_completeness_state == "WATCH":
        return "Review data quality trends and confirm telemetry consistency during shifts."
    if data_completeness_state == "UNKNOWN":
        return "Confirm daily KPI completeness before using this state for planning decisions."
    if freshness_status == "STALE":
        return "Keep operations stable and prioritize telemetry refresh in the next cycle."
    return "Continue normal operation with routine monitoring of pressure, tank level, and turbidity."


def _compute_confidence_score(
    freshness_status: str,
    pressure_low: bool,
    pressure_critical: bool,
    tank_low: bool,
    tank_critical: bool,
    projected_tank_low: bool,
    projected_tank_critical: bool,
    turbidity_high: bool,
    turbidity_critical: bool,
    data_completeness_state: str,
) -> float:
    # Fixed additive penalties keep confidence transparent and auditable.
    score = 0.95
    if freshness_status == "STALE":
        score -= 0.15
    elif freshness_status == "OUTDATED":
        score -= 0.40

    if pressure_low:
        score -= 0.12
    if pressure_critical:
        score -= 0.10

    if tank_low:
        score -= 0.10
    if tank_critical:
        score -= 0.12
    if projected_tank_low and not tank_low:
        score -= 0.06
    if projected_tank_critical and not tank_critical:
        score -= 0.08

    if turbidity_high:
        score -= 0.10
    if turbidity_critical:
        score -= 0.12

    if data_completeness_state == "WATCH":
        score -= 0.08
    elif data_completeness_state == "AT_RISK":
        score -= 0.15
    elif data_completeness_state == "UNKNOWN":
        score -= 0.05

    return round(max(0.0, min(1.0, score)), 3)


def _empty_state(
    apr_id: str | None,
    *,
    reason_code: str = "NO_DATA_SILVER",
    recommendation: str = "Validate data availability before issuing operational decisions.",
) -> TwinState:
    reason_codes = [reason_code] if reason_code else []
    return TwinState(
        timestamp=datetime.now(),
        apr_id=apr_id or "UNKNOWN",
        system_status="NO_DATA",
        freshness_status="NO_DATA",
        confidence="LOW",
        confidence_score=0.0,
        reason_codes=reason_codes,
        operational_recommendation=recommendation,
        active_alerts=["No Silver telemetry data available."],
    )


def _compute_freshness(data_age_minutes: float) -> str:
    if data_age_minutes <= FRESHNESS_FRESH_MAX_MINUTES:
        return "FRESH"
    if data_age_minutes <= FRESHNESS_STALE_MAX_MINUTES:
        return "STALE"
    return "OUTDATED"


def compute_current_state(apr_id: str | None = None) -> TwinState:
    cfg = ensure_data_dirs()
    silver_df = read_parquet_file(cfg.silver_file)
    if silver_df.empty:
        LOGGER.warning("Silver dataset is empty, returning NO_DATA twin state.")
        return _empty_state(apr_id)

    silver_df = silver_df.copy()
    silver_df["timestamp"] = pd.to_datetime(silver_df["timestamp"], errors="coerce")
    silver_df = silver_df.dropna(subset=["timestamp"]).sort_values("timestamp")
    if silver_df.empty:
        return _empty_state(apr_id)

    selected_apr = apr_id or str(silver_df.iloc[-1]["apr_id"])
    apr_df = silver_df[silver_df["apr_id"] == selected_apr].copy()
    if apr_df.empty:
        LOGGER.warning("APR id %s not found in Silver data.", selected_apr)
        return _empty_state(
            selected_apr,
            reason_code="APR_NOT_FOUND_IN_SILVER",
            recommendation="Select an APR with telemetry coverage in the current Silver dataset.",
        )

    latest = apr_df.iloc[-1]
    latest_ts = pd.Timestamp(latest["timestamp"])
    now_ts = pd.Timestamp.now()
    data_age_minutes = max(0.0, float((now_ts - latest_ts).total_seconds() / 60.0))
    freshness_status = _compute_freshness(data_age_minutes)

    gold_df = read_parquet_file(cfg.gold_daily_file)
    pressure_compliance_ratio: float | None = None
    daily_volume_m3: float | None = None
    risk_level: str | None = None
    completeness_pct: float | None = None
    imputed_pct: float | None = None
    if not gold_df.empty:
        gold_df = gold_df.copy()
        gold_df["date"] = pd.to_datetime(gold_df["date"], errors="coerce").dt.floor("D")
        today = latest_ts.floor("D")
        gold_apr = gold_df[gold_df["apr_id"] == selected_apr].sort_values("date")
        if not gold_apr.empty:
            today_row = gold_apr[gold_apr["date"] == today]
            kpi_row = today_row.iloc[-1] if not today_row.empty else gold_apr.iloc[-1]
            pressure_compliance_ratio = float(kpi_row["pressure_ok_ratio"])
            daily_volume_m3 = float(kpi_row["daily_volume_m3"])
            risk_level = str(kpi_row["risk_level"])
            completeness_pct = float(kpi_row["completeness_pct"]) if pd.notna(kpi_row.get("completeness_pct")) else None
            imputed_pct = float(kpi_row["imputed_pct"]) if pd.notna(kpi_row.get("imputed_pct")) else None

    current_pressure = float(latest["pressure_bar"])
    current_tank = float(latest["tank_level_pct"])
    current_turbidity = float(latest["turbidity_ntu"])
    projected_tank_level_2h_pct = _project_tank_level_2h(apr_df=apr_df, latest_ts=latest_ts, current_tank=current_tank)

    pressure_low = current_pressure < PRESSURE_MIN_BAR
    pressure_critical = current_pressure < 1.0
    tank_low = current_tank < TANK_LOW_PCT
    tank_critical = current_tank <= TANK_CRITICAL_PCT
    projected_tank_low = (
        projected_tank_level_2h_pct is not None and projected_tank_level_2h_pct < TANK_LOW_PCT
    )
    projected_tank_critical = (
        projected_tank_level_2h_pct is not None and projected_tank_level_2h_pct <= TANK_CRITICAL_PCT
    )
    turbidity_high = current_turbidity > TURBIDITY_ALERT_NTU
    turbidity_critical = current_turbidity >= TURBIDITY_CRITICAL_NTU
    data_completeness_state = _classify_data_completeness(completeness_pct=completeness_pct, imputed_pct=imputed_pct)

    alerts: list[str] = []
    reason_codes: list[str] = []
    if pressure_low:
        alerts.append("Low pressure")
        _append_reason(reason_codes, "PRESSURE_LOW")
    if pressure_critical:
        _append_reason(reason_codes, "PRESSURE_CRITICAL")

    if tank_low:
        alerts.append("Low tank level")
        _append_reason(reason_codes, "TANK_LOW")
    if tank_critical:
        _append_reason(reason_codes, "TANK_CRITICAL")
    if projected_tank_low:
        _append_reason(reason_codes, "PROJECTED_TANK_LOW_2H")
    if projected_tank_critical:
        _append_reason(reason_codes, "PROJECTED_TANK_CRITICAL_2H")

    if turbidity_high:
        alerts.append("High turbidity")
        _append_reason(reason_codes, "TURBIDITY_HIGH")
    if turbidity_critical:
        _append_reason(reason_codes, "TURBIDITY_CRITICAL")

    if pressure_compliance_ratio is not None and pressure_compliance_ratio < 0.95:
        alerts.append("Pressure compliance below target")
        _append_reason(reason_codes, "PRESSURE_COMPLIANCE_BELOW_TARGET")
    if risk_level in {"MEDIUM", "HIGH"}:
        alerts.append(f"Daily risk level: {risk_level}")
        _append_reason(reason_codes, f"DAILY_RISK_{risk_level}")
    if data_completeness_state == "WATCH":
        _append_reason(reason_codes, "DATA_COMPLETENESS_WATCH")
    elif data_completeness_state == "AT_RISK":
        _append_reason(reason_codes, "DATA_COMPLETENESS_AT_RISK")
    elif data_completeness_state == "UNKNOWN":
        _append_reason(reason_codes, "DATA_COMPLETENESS_UNKNOWN")

    if turbidity_critical or tank_critical or projected_tank_critical or pressure_critical:
        status = "CRITICAL"
    elif alerts:
        status = "WARNING"
    else:
        status = "OK"

    if freshness_status == "STALE":
        alerts.append("Telemetry data is stale")
        _append_reason(reason_codes, "FRESHNESS_STALE")
        if status == "OK":
            status = "WARNING"
    elif freshness_status == "OUTDATED":
        alerts.append("Telemetry data is outdated")
        _append_reason(reason_codes, "FRESHNESS_OUTDATED")
        if status in {"OK", "WARNING"}:
            status = "CRITICAL"

    confidence_score = _compute_confidence_score(
        freshness_status=freshness_status,
        pressure_low=pressure_low,
        pressure_critical=pressure_critical,
        tank_low=tank_low,
        tank_critical=tank_critical,
        projected_tank_low=projected_tank_low,
        projected_tank_critical=projected_tank_critical,
        turbidity_high=turbidity_high,
        turbidity_critical=turbidity_critical,
        data_completeness_state=data_completeness_state,
    )
    confidence = _confidence_label(confidence_score)
    operational_recommendation = _build_operational_recommendation(
        freshness_status=freshness_status,
        pressure_low=pressure_low,
        pressure_critical=pressure_critical,
        tank_low=tank_low,
        tank_critical=tank_critical,
        projected_tank_low=projected_tank_low,
        projected_tank_critical=projected_tank_critical,
        turbidity_high=turbidity_high,
        turbidity_critical=turbidity_critical,
        data_completeness_state=data_completeness_state,
    )

    return TwinState(
        timestamp=latest_ts.to_pydatetime(),
        apr_id=selected_apr,
        system_status=status,
        current_tank_level_pct=current_tank,
        current_pressure_bar=current_pressure,
        current_turbidity_ntu=current_turbidity,
        pressure_compliance_ratio=pressure_compliance_ratio,
        daily_volume_m3=daily_volume_m3,
        data_age_minutes=round(data_age_minutes, 3),
        freshness_status=freshness_status,
        confidence=confidence,
        confidence_score=confidence_score,
        projected_tank_level_2h_pct=projected_tank_level_2h_pct,
        reason_codes=reason_codes,
        operational_recommendation=operational_recommendation,
        turbidity_alert_active=current_turbidity > TURBIDITY_ALERT_NTU,
        active_alerts=alerts,
    )


