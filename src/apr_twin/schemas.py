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
    confidence: float = 0.0
    turbidity_alert_active: bool = False
    active_alerts: list[str] = Field(default_factory=list)
