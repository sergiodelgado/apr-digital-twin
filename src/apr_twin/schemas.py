from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "warning"]
    bronze_files: int
    silver_rows: int
    gold_rows: int
    last_telemetry_timestamp: datetime | None = None


class TelemetryRecord(BaseModel):
    timestamp: datetime
    apr_id: str
    sensor_id: str
    batch_id: str
    source_file: str
    processed_at: datetime
    flow_lps: float
    pressure_bar: float
    tank_level_pct: float
    turbidity_ntu: float
    pump_on: bool
    pressure_ok: bool
    turbidity_alert: bool
    is_synthetic: bool


class DailyKPIRecord(BaseModel):
    date: date
    apr_id: str
    batch_id: str
    source_file: str
    processed_at: datetime
    records: int
    avg_flow_lps: float
    daily_volume_m3: float
    avg_pressure_bar: float
    pressure_ok_ratio: float
    min_tank_level_pct: float
    max_tank_level_pct: float
    pump_runtime_h: float
    avg_turbidity_ntu: float
    turbidity_alert_count: int
    completeness_pct: float
    imputed_pct: float
    low_pressure_duration_minutes: float
    high_turbidity_duration_minutes: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


class AvailableAPRRecord(BaseModel):
    apr_id: str
    telemetry_records: int
    kpi_records: int
    first_telemetry_timestamp: datetime | None = None
    last_telemetry_timestamp: datetime | None = None
    first_kpi_date: date | None = None
    last_kpi_date: date | None = None


class TwinState(BaseModel):
    timestamp: datetime = Field(description="Last telemetry timestamp used for the twin state.")
    apr_id: str
    system_status: Literal["OK", "WARNING", "CRITICAL", "NO_DATA"]
    current_tank_level_pct: float | None = None
    current_pressure_bar: float | None = None
    current_turbidity_ntu: float | None = None
    pressure_compliance_ratio: float | None = None
    daily_volume_m3: float | None = None
    data_age_minutes: float | None = None
    freshness_status: Literal["FRESH", "STALE", "OUTDATED", "NO_DATA"] = "NO_DATA"
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    confidence_score: float = 0.0
    projected_tank_level_2h_pct: float | None = None
    observed_tank_trend_pct_per_hour: float | None = None
    tank_balance_consistency: Literal["CONSISTENT", "WATCH", "INCONSISTENT", "UNKNOWN"] = "UNKNOWN"
    hydraulic_risk: Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"] = "UNKNOWN"
    possible_root_cause: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    operational_recommendation: str | None = None
    turbidity_alert_active: bool = False
    active_alerts: list[str] = Field(default_factory=list)
