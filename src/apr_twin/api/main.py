from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from apr_twin.config import ensure_data_dirs
from apr_twin.schemas import AvailableAPRRecord, DailyKPIRecord, HealthResponse, TelemetryRecord, TwinState
from apr_twin.storage.parquet_io import read_parquet_file
from apr_twin.twin.engine import compute_current_state
from apr_twin.utils.logging_utils import configure_logging

configure_logging()
LOGGER = logging.getLogger(__name__)

app = FastAPI(title="APR Digital Twin API", version="0.1.0")


def _as_naive_timestamp(value: datetime | date) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tz is not None:
        ts = ts.tz_convert(None)
    return ts


def _validate_range(start: datetime | date | None, end: datetime | date | None) -> None:
    if start is not None and end is not None and end < start:
        raise HTTPException(status_code=400, detail="Invalid range: end must be greater than or equal to start.")


def _load_silver() -> pd.DataFrame:
    cfg = ensure_data_dirs()
    df = read_parquet_file(cfg.silver_file)
    if df.empty:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "processed_at" not in df.columns:
        df["processed_at"] = pd.NaT
    df["processed_at"] = pd.to_datetime(df["processed_at"], errors="coerce", utc=True).dt.tz_convert(None)
    if "batch_id" not in df.columns:
        df["batch_id"] = "unknown"
    if "source_file" not in df.columns:
        df["source_file"] = "unknown"
    df["batch_id"] = df["batch_id"].fillna("").astype(str).str.strip().replace("", "unknown")
    df["source_file"] = df["source_file"].fillna("").astype(str).str.strip().replace("", "unknown")
    fallback_processed = pd.Timestamp.now().floor("s")
    df["processed_at"] = df["processed_at"].fillna(fallback_processed)
    return df.dropna(subset=["timestamp"])


def _load_gold_daily() -> pd.DataFrame:
    cfg = ensure_data_dirs()
    df = read_parquet_file(cfg.gold_daily_file)
    if df.empty:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "processed_at" not in df.columns:
        df["processed_at"] = pd.NaT
    df["processed_at"] = pd.to_datetime(df["processed_at"], errors="coerce", utc=True).dt.tz_convert(None)
    if "batch_id" not in df.columns:
        df["batch_id"] = "unknown"
    if "source_file" not in df.columns:
        df["source_file"] = "unknown"
    df["batch_id"] = df["batch_id"].fillna("").astype(str).str.strip().replace("", "unknown")
    df["source_file"] = df["source_file"].fillna("").astype(str).str.strip().replace("", "unknown")
    fallback_processed = pd.Timestamp.now().floor("s")
    df["processed_at"] = df["processed_at"].fillna(fallback_processed)
    return df.dropna(subset=["date"])


@app.get("/aprs/available", response_model=list[AvailableAPRRecord])
def aprs_available() -> list[AvailableAPRRecord]:
    silver_df = _load_silver()
    gold_df = _load_gold_daily()

    apr_ids: set[str] = set()
    if not silver_df.empty:
        apr_ids.update(silver_df["apr_id"].dropna().astype(str).str.strip())
    if not gold_df.empty:
        apr_ids.update(gold_df["apr_id"].dropna().astype(str).str.strip())
    apr_ids.discard("")

    results: list[AvailableAPRRecord] = []
    for apr_id in sorted(apr_ids):
        silver_apr = silver_df[silver_df["apr_id"] == apr_id] if not silver_df.empty else pd.DataFrame()
        gold_apr = gold_df[gold_df["apr_id"] == apr_id] if not gold_df.empty else pd.DataFrame()

        first_telemetry = (
            pd.Timestamp(silver_apr["timestamp"].min()).to_pydatetime() if not silver_apr.empty else None
        )
        last_telemetry = (
            pd.Timestamp(silver_apr["timestamp"].max()).to_pydatetime() if not silver_apr.empty else None
        )
        first_kpi_date = pd.Timestamp(gold_apr["date"].min()).date() if not gold_apr.empty else None
        last_kpi_date = pd.Timestamp(gold_apr["date"].max()).date() if not gold_apr.empty else None

        results.append(
            AvailableAPRRecord(
                apr_id=apr_id,
                telemetry_records=int(len(silver_apr)),
                kpi_records=int(len(gold_apr)),
                first_telemetry_timestamp=first_telemetry,
                last_telemetry_timestamp=last_telemetry,
                first_kpi_date=first_kpi_date,
                last_kpi_date=last_kpi_date,
            )
        )

    return results


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
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> list[TelemetryRecord]:
    _validate_range(start=start, end=end)
    df = _load_silver()
    if df.empty:
        return []

    if apr_id:
        df = df[df["apr_id"] == apr_id]
    if start is not None:
        df = df[df["timestamp"] >= _as_naive_timestamp(start)]
    if end is not None:
        df = df[df["timestamp"] <= _as_naive_timestamp(end)]
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
                batch_id=str(row["batch_id"]),
                source_file=str(row["source_file"]),
                processed_at=pd.Timestamp(row["processed_at"]).to_pydatetime(),
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
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> list[DailyKPIRecord]:
    _validate_range(start=start, end=end)
    df = _load_gold_daily()
    if df.empty:
        return []

    if apr_id:
        df = df[df["apr_id"] == apr_id]
    if start is not None:
        df = df[df["date"] >= _as_naive_timestamp(start).floor("D")]
    if end is not None:
        df = df[df["date"] <= _as_naive_timestamp(end).floor("D")]
    if df.empty:
        return []

    if start is None and end is None:
        cutoff = pd.Timestamp.now().floor("D") - pd.Timedelta(days=days - 1)
        df = df[df["date"] >= cutoff]
    df = df.sort_values("date")
    results: list[DailyKPIRecord] = []
    for row in df.to_dict(orient="records"):
        results.append(
            DailyKPIRecord(
                date=pd.Timestamp(row["date"]).date(),
                apr_id=str(row["apr_id"]),
                batch_id=str(row["batch_id"]),
                source_file=str(row["source_file"]),
                processed_at=pd.Timestamp(row["processed_at"]).to_pydatetime(),
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

