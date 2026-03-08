from __future__ import annotations

import logging
from datetime import datetime

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


def _empty_state(apr_id: str | None) -> TwinState:
    return TwinState(
        timestamp=datetime.now(),
        apr_id=apr_id or "UNKNOWN",
        system_status="NO_DATA",
        freshness_status="NO_DATA",
        confidence=0.0,
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
        return _empty_state(selected_apr)

    latest = apr_df.iloc[-1]
    latest_ts = pd.Timestamp(latest["timestamp"])
    now_ts = pd.Timestamp.now()
    data_age_minutes = max(0.0, float((now_ts - latest_ts).total_seconds() / 60.0))
    freshness_status = _compute_freshness(data_age_minutes)

    gold_df = read_parquet_file(cfg.gold_daily_file)
    pressure_compliance_ratio: float | None = None
    daily_volume_m3: float | None = None
    risk_level: str | None = None
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

    current_pressure = float(latest["pressure_bar"])
    current_tank = float(latest["tank_level_pct"])
    current_turbidity = float(latest["turbidity_ntu"])

    alerts: list[str] = []
    if current_pressure < PRESSURE_MIN_BAR:
        alerts.append("Low pressure")
    if current_tank < TANK_LOW_PCT:
        alerts.append("Low tank level")
    if current_turbidity > TURBIDITY_ALERT_NTU:
        alerts.append("High turbidity")
    if pressure_compliance_ratio is not None and pressure_compliance_ratio < 0.95:
        alerts.append("Pressure compliance below target")
    if risk_level in {"MEDIUM", "HIGH"}:
        alerts.append(f"Daily risk level: {risk_level}")

    if (
        current_turbidity >= TURBIDITY_CRITICAL_NTU
        or current_tank <= TANK_CRITICAL_PCT
        or current_pressure < 1.0
    ):
        status = "CRITICAL"
    elif alerts:
        status = "WARNING"
    else:
        status = "OK"

    confidence = 0.95
    if status == "WARNING":
        confidence -= 0.15
    if status == "CRITICAL":
        confidence -= 0.35

    if freshness_status == "STALE":
        alerts.append("Telemetry data is stale")
        confidence -= 0.30
        if status == "OK":
            status = "WARNING"
    elif freshness_status == "OUTDATED":
        alerts.append("Telemetry data is outdated")
        confidence -= 0.55
        if status in {"OK", "WARNING"}:
            status = "CRITICAL"

    confidence = max(0.0, min(1.0, round(confidence, 3)))

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
        turbidity_alert_active=current_turbidity > TURBIDITY_ALERT_NTU,
        active_alerts=alerts,
    )


