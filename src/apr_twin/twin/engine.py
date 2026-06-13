from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

import pandas as pd

from apr_twin.config import (
    ABNORMAL_TANK_DROP_CRITICAL_PCT_PER_HOUR,
    ABNORMAL_TANK_DROP_WARN_PCT_PER_HOUR,
    FRESHNESS_FRESH_MAX_MINUTES,
    FRESHNESS_STALE_MAX_MINUTES,
    HYDRAULIC_TREND_WINDOW_HOURS,
    INSUFFICIENT_RECOVERY_MAX_TREND_PCT_PER_HOUR,
    NORMAL_STORAGE_MIN_PCT,
    PUMP_RECOVERY_MIN_TREND_PCT_PER_HOUR,
    PRESSURE_MIN_BAR,
    TANK_CRITICAL_PCT,
    TANK_LOW_PCT,
    TURBIDITY_ALERT_NTU,
    TURBIDITY_CRITICAL_NTU,
    ensure_data_dirs,
)
from apr_twin.schemas import TwinState
from apr_twin.storage.parquet_io import read_parquet_file
from apr_twin.twin.taxonomy import (
    HYDRAULIC_HIGH_RISK_REASON_CODES,
    HYDRAULIC_MEDIUM_RISK_REASON_CODES,
    ReasonCode,
    RecommendationText,
    derive_main_root_cause,
    recommendation_for_root_cause,
)

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


def _coerce_bool(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    return bool(value)


def _select_recent_hydraulic_window(apr_df: pd.DataFrame, latest_ts: pd.Timestamp) -> pd.DataFrame:
    recent = apr_df[
        apr_df["timestamp"] >= (latest_ts - pd.Timedelta(hours=HYDRAULIC_TREND_WINDOW_HOURS))
    ][["timestamp", "tank_level_pct", "pump_on"]].copy()
    recent = recent.dropna(subset=["timestamp", "tank_level_pct"]).sort_values("timestamp")
    if len(recent) < 2:
        recent = (
            apr_df[["timestamp", "tank_level_pct", "pump_on"]]
            .dropna(subset=["timestamp", "tank_level_pct"])
            .sort_values("timestamp")
            .tail(24)
        )
    return recent


def _compute_observed_tank_trend_pct_per_hour(recent_window: pd.DataFrame) -> float | None:
    if len(recent_window) < 2:
        return None

    first = recent_window.iloc[0]
    last = recent_window.iloc[-1]
    first_ts = pd.Timestamp(first["timestamp"])
    last_ts = pd.Timestamp(last["timestamp"])
    hours = float((last_ts - first_ts).total_seconds() / 3600.0)
    if hours <= 0:
        return None

    first_tank = float(first["tank_level_pct"])
    last_tank = float(last["tank_level_pct"])
    trend = (last_tank - first_tank) / hours
    return round(trend, 3)


def _is_erratic_tank_sensor_signal(recent_window: pd.DataFrame) -> bool:
    if len(recent_window) < 8:
        return False

    tank_series = pd.to_numeric(recent_window["tank_level_pct"], errors="coerce").dropna()
    if len(tank_series) < 8:
        return False

    deltas = tank_series.diff().dropna()
    if len(deltas) < 6:
        return False

    signs = deltas.apply(lambda value: 1 if value > 0 else (-1 if value < 0 else 0))
    sign_changes = int(((signs * signs.shift(1)) < 0).sum())
    abs_step_median = float(deltas.abs().median())
    net_change = float(tank_series.iloc[-1] - tank_series.iloc[0])
    span = float(tank_series.max() - tank_series.min())

    # Detect oscillatory behavior with large step-to-step swings and low net change.
    return sign_changes >= 5 and abs_step_median >= 1.5 and span >= 8.0 and abs(net_change) <= 4.0


def _project_tank_level_2h(apr_df: pd.DataFrame, latest_ts: pd.Timestamp, current_tank: float) -> float | None:
    recent = _select_recent_hydraulic_window(apr_df=apr_df, latest_ts=latest_ts)[["timestamp", "tank_level_pct"]].copy()
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


def _evaluate_hydraulic_consistency(
    *,
    observed_tank_trend_pct_per_hour: float | None,
    tank_sensor_erratic: bool,
    current_pump_on: bool,
    recent_pump_on_ratio: float | None,
    current_pressure: float,
    current_tank: float,
    projected_tank_low: bool,
) -> dict[str, object]:
    pump_on_no_recovery = False
    abnormal_drop_warn = False
    abnormal_drop_critical = False
    low_pressure_with_normal_storage = False
    projected_depletion_insufficient_recovery = False

    if observed_tank_trend_pct_per_hour is not None:
        if current_pump_on and observed_tank_trend_pct_per_hour < PUMP_RECOVERY_MIN_TREND_PCT_PER_HOUR:
            pump_on_no_recovery = True
        if observed_tank_trend_pct_per_hour <= -ABNORMAL_TANK_DROP_CRITICAL_PCT_PER_HOUR:
            abnormal_drop_critical = True
        elif observed_tank_trend_pct_per_hour <= -ABNORMAL_TANK_DROP_WARN_PCT_PER_HOUR:
            abnormal_drop_warn = True

        enough_recent_pumping = (recent_pump_on_ratio or 0.0) >= 0.5
        if (
            projected_tank_low
            and (current_pump_on or enough_recent_pumping)
            and observed_tank_trend_pct_per_hour < INSUFFICIENT_RECOVERY_MAX_TREND_PCT_PER_HOUR
        ):
            projected_depletion_insufficient_recovery = True

    low_pressure_with_normal_storage = current_pressure < PRESSURE_MIN_BAR and current_tank >= NORMAL_STORAGE_MIN_PCT

    if observed_tank_trend_pct_per_hour is None:
        tank_balance_consistency: Literal["CONSISTENT", "WATCH", "INCONSISTENT", "UNKNOWN"] = "UNKNOWN"
        hydraulic_risk: Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"] = "UNKNOWN"
    elif any(
        (
            pump_on_no_recovery,
            abnormal_drop_critical,
            low_pressure_with_normal_storage,
            projected_depletion_insufficient_recovery,
            tank_sensor_erratic,
        )
    ):
        tank_balance_consistency = "INCONSISTENT"
        hydraulic_risk = "HIGH" if abnormal_drop_critical or projected_depletion_insufficient_recovery else "MEDIUM"
    elif abnormal_drop_warn:
        tank_balance_consistency = "WATCH"
        hydraulic_risk = "MEDIUM"
    else:
        tank_balance_consistency = "CONSISTENT"
        hydraulic_risk = "LOW"

    if projected_depletion_insufficient_recovery:
        possible_root_cause = "Net outflow is exceeding recovery capacity."
    elif pump_on_no_recovery:
        possible_root_cause = "Pump is running but storage is not recovering as expected."
    elif low_pressure_with_normal_storage:
        possible_root_cause = "Distribution-side hydraulic losses are likely despite normal storage."
    elif tank_sensor_erratic:
        possible_root_cause = "Tank level sensor appears noisy or erratic."
    elif abnormal_drop_critical or abnormal_drop_warn:
        possible_root_cause = "Tank level is dropping faster than typical demand behavior."
    elif observed_tank_trend_pct_per_hour is None:
        possible_root_cause = "Not enough recent telemetry to infer hydraulic behavior."
    elif observed_tank_trend_pct_per_hour >= 0:
        possible_root_cause = "Recent tank trend is consistent with recovery."
    else:
        possible_root_cause = "Recent tank decline appears demand-driven under current operation."

    return {
        "pump_on_no_recovery": pump_on_no_recovery,
        "abnormal_drop_warn": abnormal_drop_warn,
        "abnormal_drop_critical": abnormal_drop_critical,
        "low_pressure_with_normal_storage": low_pressure_with_normal_storage,
        "projected_depletion_insufficient_recovery": projected_depletion_insufficient_recovery,
        "tank_sensor_erratic": tank_sensor_erratic,
        "tank_balance_consistency": tank_balance_consistency,
        "hydraulic_risk": hydraulic_risk,
        "possible_root_cause": possible_root_cause,
    }


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
    pump_on_no_recovery: bool,
    abnormal_drop_warn: bool,
    abnormal_drop_critical: bool,
    low_pressure_with_normal_storage: bool,
    projected_depletion_insufficient_recovery: bool,
    tank_sensor_erratic: bool,
    hydraulic_risk: str,
    possible_root_cause: str | None,
) -> str:
    if freshness_status == "OUTDATED":
        return RecommendationText.TELEMETRY_OUTDATED
    if projected_depletion_insufficient_recovery:
        return RecommendationText.PROJECTED_DEPLETION
    if pump_on_no_recovery:
        return RecommendationText.PUMP_NO_RECOVERY
    if low_pressure_with_normal_storage:
        return RecommendationText.DISTRIBUTION_HYDRAULICS
    if tank_sensor_erratic:
        return RecommendationText.TANK_SENSOR_ERRATIC
    if abnormal_drop_critical:
        return RecommendationText.TANK_DROP_CRITICAL
    if abnormal_drop_warn:
        return RecommendationText.TANK_DROP_WARN
    if pressure_critical:
        return RecommendationText.PRESSURE_CRITICAL
    if pressure_low:
        return RecommendationText.PRESSURE_LOW
    if tank_critical or projected_tank_critical:
        return RecommendationText.TANK_CRITICAL
    if tank_low or projected_tank_low:
        return RecommendationText.TANK_LOW
    if turbidity_critical:
        return RecommendationText.TURBIDITY_CRITICAL
    if turbidity_high:
        return RecommendationText.TURBIDITY_HIGH
    if data_completeness_state == "AT_RISK":
        return RecommendationText.DATA_QUALITY_AT_RISK
    if data_completeness_state == "WATCH":
        return RecommendationText.DATA_QUALITY_WATCH
    if data_completeness_state == "UNKNOWN":
        return RecommendationText.DATA_QUALITY_UNKNOWN
    if freshness_status == "STALE":
        return RecommendationText.TELEMETRY_STALE
    if hydraulic_risk in {"MEDIUM", "HIGH"} and possible_root_cause:
        return f"Hydraulic inconsistency detected. Likely cause: {possible_root_cause}"
    return RecommendationText.NORMAL_OPERATION


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
    tank_balance_consistency: str,
    hydraulic_risk: str,
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

    if tank_balance_consistency == "WATCH":
        score -= 0.05
    elif tank_balance_consistency == "INCONSISTENT":
        score -= 0.10

    if hydraulic_risk == "MEDIUM":
        score -= 0.06
    elif hydraulic_risk == "HIGH":
        score -= 0.10

    return round(max(0.0, min(1.0, score)), 3)


def _empty_state(
    apr_id: str | None,
    *,
    reason_code: str = ReasonCode.TELEMETRY_NO_DATA,
    recommendation: str = RecommendationText.DATA_UNAVAILABLE,
) -> TwinState:
    reason_codes = [reason_code] if reason_code else []
    return TwinState(
        timestamp=datetime.now(),
        apr_id=apr_id or "UNKNOWN",
        system_status="NO_DATA",
        freshness_status="NO_DATA",
        confidence="LOW",
        confidence_score=0.0,
        tank_balance_consistency="UNKNOWN",
        hydraulic_risk="UNKNOWN",
        possible_root_cause="No telemetry available to infer hydraulic behavior.",
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
            reason_code=ReasonCode.APR_NOT_FOUND,
            recommendation=RecommendationText.APR_NOT_FOUND,
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
    current_pump_on = _coerce_bool(latest.get("pump_on"))
    recent_hydraulic_window = _select_recent_hydraulic_window(apr_df=apr_df, latest_ts=latest_ts)
    observed_tank_trend_pct_per_hour = _compute_observed_tank_trend_pct_per_hour(recent_hydraulic_window)
    tank_sensor_erratic = _is_erratic_tank_sensor_signal(recent_hydraulic_window)
    recent_pump_on_ratio: float | None = None
    if not recent_hydraulic_window.empty:
        pump_series = recent_hydraulic_window["pump_on"].map(_coerce_bool).astype(float)
        if not pump_series.empty:
            recent_pump_on_ratio = round(float(pump_series.mean()), 3)
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
    hydraulic_eval = _evaluate_hydraulic_consistency(
        observed_tank_trend_pct_per_hour=observed_tank_trend_pct_per_hour,
        tank_sensor_erratic=tank_sensor_erratic,
        current_pump_on=current_pump_on,
        recent_pump_on_ratio=recent_pump_on_ratio,
        current_pressure=current_pressure,
        current_tank=current_tank,
        projected_tank_low=projected_tank_low,
    )
    pump_on_no_recovery = bool(hydraulic_eval["pump_on_no_recovery"])
    abnormal_drop_warn = bool(hydraulic_eval["abnormal_drop_warn"])
    abnormal_drop_critical = bool(hydraulic_eval["abnormal_drop_critical"])
    low_pressure_with_normal_storage = bool(hydraulic_eval["low_pressure_with_normal_storage"])
    projected_depletion_insufficient_recovery = bool(hydraulic_eval["projected_depletion_insufficient_recovery"])
    tank_sensor_erratic = bool(hydraulic_eval["tank_sensor_erratic"])
    tank_balance_consistency = str(hydraulic_eval["tank_balance_consistency"])
    hydraulic_risk = str(hydraulic_eval["hydraulic_risk"])
    possible_root_cause = str(hydraulic_eval["possible_root_cause"])

    alerts: list[str] = []
    reason_codes: list[str] = []
    if pressure_low:
        alerts.append("Low pressure")
        _append_reason(reason_codes, ReasonCode.PRESSURE_LOW)
    if pressure_critical:
        _append_reason(reason_codes, ReasonCode.PRESSURE_CRITICAL)

    if tank_low:
        alerts.append("Low tank level")
        _append_reason(reason_codes, ReasonCode.TANK_LOW)
    if tank_critical:
        _append_reason(reason_codes, ReasonCode.TANK_CRITICAL)
    if projected_tank_low:
        alerts.append("Projected low tank level in 2 hours")
        _append_reason(reason_codes, ReasonCode.TANK_PROJECTED_LOW_2H)
    if projected_tank_critical:
        alerts.append("Projected critical tank level in 2 hours")
        _append_reason(reason_codes, ReasonCode.TANK_PROJECTED_CRITICAL_2H)

    if pump_on_no_recovery:
        alerts.append("Pump on but tank level not recovering")
        _append_reason(reason_codes, ReasonCode.PUMP_NO_RECOVERY)
    if abnormal_drop_warn:
        alerts.append("Abnormal tank drop rate")
        _append_reason(reason_codes, ReasonCode.TANK_DROP_WARN)
    if abnormal_drop_critical:
        _append_reason(reason_codes, ReasonCode.TANK_DROP_CRITICAL)
    if low_pressure_with_normal_storage:
        alerts.append("Low pressure with normal storage")
        _append_reason(reason_codes, ReasonCode.PRESSURE_LOW_NORMAL_STORAGE)
    if projected_depletion_insufficient_recovery:
        alerts.append("Projected depletion risk with insufficient recovery")
        _append_reason(reason_codes, ReasonCode.DEPLETION_WEAK_RECOVERY)
    if tank_sensor_erratic:
        alerts.append("Noisy or erratic tank level signal")
        _append_reason(reason_codes, ReasonCode.TANK_SENSOR_ERRATIC)

    if tank_balance_consistency == "WATCH":
        _append_reason(reason_codes, ReasonCode.HYDRAULIC_BALANCE_WATCH)
    elif tank_balance_consistency == "INCONSISTENT":
        _append_reason(reason_codes, ReasonCode.HYDRAULIC_BALANCE_INCONSISTENT)
    if hydraulic_risk in {"MEDIUM", "HIGH"}:
        risk_reason = {
            "MEDIUM": ReasonCode.HYDRAULIC_RISK_MEDIUM,
            "HIGH": ReasonCode.HYDRAULIC_RISK_HIGH,
        }[hydraulic_risk]
        _append_reason(reason_codes, risk_reason)

    if turbidity_high:
        alerts.append("High turbidity")
        _append_reason(reason_codes, ReasonCode.TURBIDITY_HIGH)
    if turbidity_critical:
        _append_reason(reason_codes, ReasonCode.TURBIDITY_CRITICAL)

    if pressure_compliance_ratio is not None and pressure_compliance_ratio < 0.95:
        alerts.append("Pressure compliance below target")
        _append_reason(reason_codes, ReasonCode.PRESSURE_COMPLIANCE_LOW)
    if risk_level in {"MEDIUM", "HIGH"}:
        alerts.append(f"Daily risk level: {risk_level}")
        daily_risk_reason = {
            "MEDIUM": ReasonCode.KPI_RISK_MEDIUM,
            "HIGH": ReasonCode.KPI_RISK_HIGH,
        }[risk_level]
        _append_reason(reason_codes, daily_risk_reason)
    if data_completeness_state == "WATCH":
        _append_reason(reason_codes, ReasonCode.DATA_QUALITY_WATCH)
    elif data_completeness_state == "AT_RISK":
        _append_reason(reason_codes, ReasonCode.DATA_QUALITY_AT_RISK)
    elif data_completeness_state == "UNKNOWN":
        _append_reason(reason_codes, ReasonCode.DATA_QUALITY_UNKNOWN)

    if turbidity_critical or tank_critical or projected_tank_critical or pressure_critical or hydraulic_risk == "HIGH":
        status = "CRITICAL"
    elif alerts:
        status = "WARNING"
    else:
        status = "OK"

    if freshness_status == "STALE":
        alerts.append("Telemetry data is stale")
        _append_reason(reason_codes, ReasonCode.FRESHNESS_STALE)
        if status == "OK":
            status = "WARNING"
    elif freshness_status == "OUTDATED":
        alerts.append("Telemetry data is outdated")
        _append_reason(reason_codes, ReasonCode.FRESHNESS_OUTDATED)
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
        tank_balance_consistency=tank_balance_consistency,
        hydraulic_risk=hydraulic_risk,
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
        pump_on_no_recovery=pump_on_no_recovery,
        abnormal_drop_warn=abnormal_drop_warn,
        abnormal_drop_critical=abnormal_drop_critical,
        low_pressure_with_normal_storage=low_pressure_with_normal_storage,
        projected_depletion_insufficient_recovery=projected_depletion_insufficient_recovery,
        tank_sensor_erratic=tank_sensor_erratic,
        hydraulic_risk=hydraulic_risk,
        possible_root_cause=possible_root_cause,
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
        observed_tank_trend_pct_per_hour=observed_tank_trend_pct_per_hour,
        tank_balance_consistency=tank_balance_consistency,
        hydraulic_risk=hydraulic_risk,
        possible_root_cause=possible_root_cause,
        reason_codes=reason_codes,
        operational_recommendation=operational_recommendation,
        turbidity_alert_active=current_turbidity > TURBIDITY_ALERT_NTU,
        active_alerts=alerts,
    )
