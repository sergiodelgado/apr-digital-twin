from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from fastapi import FastAPI, Query

from src.apr_twin.config import ensure_data_dirs
from src.apr_twin.schemas import DailyKPIRecord, HealthResponse, TelemetryRecord, TwinState
from src.apr_twin.storage.parquet_io import read_parquet_file
from src.apr_twin.twin.engine import compute_current_state
from src.apr_twin.utils.logging_utils import configure_logging

configure_logging()
LOGGER = logging.getLogger(__name__)

app = FastAPI(title="APR Digital Twin API", version="0.1.0")


def _load_silver() -> pd.DataFrame:
    cfg = ensure_data_dirs()
    df = read_parquet_file(cfg.silver_file)
    if df.empty:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"])


def _load_gold_daily() -> pd.DataFrame:
    cfg = ensure_data_dirs()
    df = read_parquet_file(cfg.gold_daily_file)
    if df.empty:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    cfg = ensure_data_dirs()
    silver_df = _load_silver()
    gold_df = _load_gold_daily()
    last_ts = None
    if not silver_df.empty:
        last_ts = pd.Timestamp(silver_df["timestamp"].max()).to_pydatetime()

    return HealthResponse(
        status="ok" if not silver_df.empty else "warning",
        bronze_files=len(list(cfg.bronze_dir.glob("*.parquet"))),
        silver_rows=len(silver_df),
        gold_rows=len(gold_df),
        last_telemetry_timestamp=last_ts,
    )


@app.get("/telemetry/recent", response_model=list[TelemetryRecord])
def telemetry_recent(
    limit: int = Query(default=200, ge=1, le=5000),
    apr_id: str | None = None,
) -> list[TelemetryRecord]:
    df = _load_silver()
    if df.empty:
        return []

    if apr_id:
        df = df[df["apr_id"] == apr_id]
    if df.empty:
        return []

    df = df.sort_values("timestamp").tail(limit)
    records: list[TelemetryRecord] = []
    for row in df.to_dict(orient="records"):
        records.append(
            TelemetryRecord(
                timestamp=pd.Timestamp(row["timestamp"]).to_pydatetime(),
                apr_id=str(row["apr_id"]),
                sensor_id=str(row["sensor_id"]),
                flow_lps=float(row["flow_lps"]),
                pressure_bar=float(row["pressure_bar"]),
                tank_level_pct=float(row["tank_level_pct"]),
                turbidity_ntu=float(row["turbidity_ntu"]),
                pump_on=bool(row["pump_on"]),
                pressure_ok=bool(row["pressure_ok"]),
                turbidity_alert=bool(row["turbidity_alert"]),
                is_synthetic=bool(row["is_synthetic"]),
            )
        )
    return records


@app.get("/kpis/daily", response_model=list[DailyKPIRecord])
def kpis_daily(
    days: int = Query(default=14, ge=1, le=365),
    apr_id: str | None = None,
) -> list[DailyKPIRecord]:
    df = _load_gold_daily()
    if df.empty:
        return []

    if apr_id:
        df = df[df["apr_id"] == apr_id]
    if df.empty:
        return []

    cutoff = pd.Timestamp.now().floor("D") - pd.Timedelta(days=days - 1)
    df = df[df["date"] >= cutoff].sort_values("date")
    results: list[DailyKPIRecord] = []
    for row in df.to_dict(orient="records"):
        results.append(
            DailyKPIRecord(
                date=pd.Timestamp(row["date"]).date(),
                apr_id=str(row["apr_id"]),
                records=int(row["records"]),
                avg_flow_lps=float(row["avg_flow_lps"]),
                daily_volume_m3=float(row["daily_volume_m3"]),
                avg_pressure_bar=float(row["avg_pressure_bar"]),
                pressure_ok_ratio=float(row["pressure_ok_ratio"]),
                min_tank_level_pct=float(row["min_tank_level_pct"]),
                max_tank_level_pct=float(row["max_tank_level_pct"]),
                pump_runtime_h=float(row["pump_runtime_h"]),
                avg_turbidity_ntu=float(row["avg_turbidity_ntu"]),
                turbidity_alert_count=int(row["turbidity_alert_count"]),
                completeness_pct=float(row["completeness_pct"]),
                imputed_pct=float(row["imputed_pct"]),
                low_pressure_duration_minutes=float(row["low_pressure_duration_minutes"]),
                high_turbidity_duration_minutes=float(row["high_turbidity_duration_minutes"]),
                risk_level=str(row["risk_level"]),
            )
        )
    return results


@app.get("/twin/state", response_model=TwinState)
def twin_state(apr_id: str | None = None) -> TwinState:
    return compute_current_state(apr_id=apr_id)


@app.get("/")
def root() -> dict[str, Any]:
    return {"message": "APR Digital Twin API", "docs": "/docs"}
