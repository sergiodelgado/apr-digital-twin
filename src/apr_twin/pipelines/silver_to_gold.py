from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from apr_twin.config import ensure_data_dirs
from apr_twin.storage.parquet_io import read_parquet_file, write_parquet

LOGGER = logging.getLogger(__name__)


def _safe_default_interval_seconds(group: pd.DataFrame) -> float:
    diffs = group["timestamp"].diff().dt.total_seconds()
    valid = diffs[(diffs > 0) & diffs.notna()]
    if valid.empty:
        return 300.0
    return float(valid.median())


def _expected_count_for_sensor_day(group: pd.DataFrame) -> int:
    if group.empty:
        return 0
    g = group.sort_values("timestamp")
    interval_seconds = _safe_default_interval_seconds(g)
    span_seconds = float((g["timestamp"].max() - g["timestamp"].min()).total_seconds())
    if span_seconds <= 0:
        return 1
    return max(1, int(round(span_seconds / interval_seconds)) + 1)


def _join_unique(values: pd.Series) -> str:
    normalized = sorted({str(v).strip() for v in values if pd.notna(v) and str(v).strip()})
    if not normalized:
        return "unknown"
    return "|".join(normalized)


def process_silver_to_gold() -> Path:
    cfg = ensure_data_dirs()
    silver_df = read_parquet_file(cfg.silver_file)
    if silver_df.empty:
        raise RuntimeError(f"Silver file not found or empty: {cfg.silver_file}")

    df = silver_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if "is_imputed" not in df.columns:
        df["is_imputed"] = False
    df["is_imputed"] = df["is_imputed"].fillna(False).astype(bool)
    if "batch_id" not in df.columns:
        df["batch_id"] = "unknown"
    if "source_file" not in df.columns:
        df["source_file"] = "unknown"

    df = df.sort_values(["apr_id", "sensor_id", "timestamp"]).reset_index(drop=True)

    group_keys = ["apr_id", "sensor_id"]
    interval_rows: list[dict[str, object]] = []
    for (apr_id, sensor_id), group in df.groupby(group_keys, sort=False):
        interval_rows.append(
            {
                "apr_id": str(apr_id),
                "sensor_id": str(sensor_id),
                "fallback_interval_seconds": _safe_default_interval_seconds(group),
            }
        )
    fallback_interval = pd.DataFrame(
        interval_rows,
        columns=["apr_id", "sensor_id", "fallback_interval_seconds"],
    )
    df = df.merge(fallback_interval, on=group_keys, how="left")

    dt_seconds = df.groupby(group_keys)["timestamp"].diff().dt.total_seconds()
    df["interval_seconds"] = dt_seconds
    first_row_mask = df["interval_seconds"].isna() | (df["interval_seconds"] <= 0)
    df.loc[first_row_mask, "interval_seconds"] = df.loc[first_row_mask, "fallback_interval_seconds"]
    df["interval_seconds"] = df["interval_seconds"].fillna(300.0)

    df["interval_minutes"] = df["interval_seconds"] / 60.0
    df["volume_m3"] = (df["flow_lps"] * df["interval_seconds"]) / 1000.0
    df["pump_runtime_h"] = (df["pump_on"].astype(int) * df["interval_seconds"]) / 3600.0
    df["low_pressure_minutes"] = (~df["pressure_ok"]).astype(int) * df["interval_minutes"]
    df["high_turbidity_minutes"] = df["turbidity_alert"].astype(int) * df["interval_minutes"]
    df["date"] = df["timestamp"].dt.floor("D")

    daily = (
        df.groupby(["apr_id", "date"], as_index=False)
        .agg(
            records=("timestamp", "count"),
            avg_flow_lps=("flow_lps", "mean"),
            daily_volume_m3=("volume_m3", "sum"),
            avg_pressure_bar=("pressure_bar", "mean"),
            pressure_ok_ratio=("pressure_ok", "mean"),
            min_tank_level_pct=("tank_level_pct", "min"),
            max_tank_level_pct=("tank_level_pct", "max"),
            pump_runtime_h=("pump_runtime_h", "sum"),
            avg_turbidity_ntu=("turbidity_ntu", "mean"),
            turbidity_alert_count=("turbidity_alert", "sum"),
            imputed_count=("is_imputed", "sum"),
            low_pressure_duration_minutes=("low_pressure_minutes", "sum"),
            high_turbidity_duration_minutes=("high_turbidity_minutes", "sum"),
            batch_id=("batch_id", _join_unique),
            source_file=("source_file", _join_unique),
        )
        .sort_values(["apr_id", "date"])
    )

    expected_rows: list[dict[str, object]] = []
    for (apr_id, sensor_id, day), group in df.groupby(["apr_id", "sensor_id", "date"], sort=False):
        expected_rows.append(
            {
                "apr_id": str(apr_id),
                "sensor_id": str(sensor_id),
                "date": day,
                "expected_records": _expected_count_for_sensor_day(group),
            }
        )
    expected_counts = pd.DataFrame(
        expected_rows,
        columns=["apr_id", "sensor_id", "date", "expected_records"],
    )
    expected_by_day = (
        expected_counts.groupby(["apr_id", "date"], as_index=False)["expected_records"].sum().rename(
            columns={"expected_records": "expected_records_total"}
        )
    )
    daily = daily.merge(expected_by_day, on=["apr_id", "date"], how="left")
    daily["expected_records_total"] = daily["expected_records_total"].fillna(daily["records"]).astype(int)

    daily["completeness_pct"] = np.where(
        daily["expected_records_total"] > 0,
        (daily["records"] / daily["expected_records_total"]) * 100.0,
        0.0,
    )
    daily["imputed_pct"] = np.where(
        daily["records"] > 0,
        (daily["imputed_count"] / daily["records"]) * 100.0,
        0.0,
    )

    high_risk = (
        (daily["pressure_ok_ratio"] < 0.85)
        | (daily["min_tank_level_pct"] < 20.0)
        | (daily["high_turbidity_duration_minutes"] >= 30.0)
        | (daily["completeness_pct"] < 85.0)
    )
    med_risk = (
        (daily["pressure_ok_ratio"] < 0.95)
        | (daily["min_tank_level_pct"] < 30.0)
        | (daily["high_turbidity_duration_minutes"] > 0.0)
        | (daily["completeness_pct"] < 95.0)
    )
    daily["risk_level"] = np.select(
        condlist=[high_risk, med_risk],
        choicelist=["HIGH", "MEDIUM"],
        default="LOW",
    )

    round_cols = [
        "avg_flow_lps",
        "daily_volume_m3",
        "avg_pressure_bar",
        "pressure_ok_ratio",
        "min_tank_level_pct",
        "max_tank_level_pct",
        "pump_runtime_h",
        "avg_turbidity_ntu",
        "completeness_pct",
        "imputed_pct",
        "low_pressure_duration_minutes",
        "high_turbidity_duration_minutes",
    ]
    daily[round_cols] = daily[round_cols].round(4)

    daily["turbidity_alert_count"] = daily["turbidity_alert_count"].astype(int)
    daily["records"] = daily["records"].astype(int)
    daily["processed_at"] = datetime.now(timezone.utc).replace(microsecond=0)

    daily = daily.drop(columns=["imputed_count", "expected_records_total"])

    write_parquet(df=daily, path=cfg.gold_daily_file)
    LOGGER.info("Gold transform completed (%d rows)", len(daily))
    return cfg.gold_daily_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform Silver telemetry to Gold KPIs.")
    parser.parse_args()
    path = process_silver_to_gold()
    print(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

