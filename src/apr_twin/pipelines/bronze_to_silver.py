from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.apr_twin.config import (
    MAX_INTERPOLATION_GAP_MINUTES,
    MAX_INTERPOLATION_STEPS,
    PRESSURE_MAX_BAR,
    PRESSURE_MIN_BAR,
    TURBIDITY_ALERT_NTU,
    ensure_data_dirs,
)
from src.apr_twin.storage.parquet_io import read_parquet_dir, write_parquet

LOGGER = logging.getLogger(__name__)


def _coerce_pump_on(series: pd.Series) -> pd.Series:
    mapped = (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map({"true": 1, "false": 0, "on": 1, "off": 0, "1": 1, "0": 0})
    )
    numeric = pd.to_numeric(series, errors="coerce")
    return mapped.fillna(numeric).fillna(0).clip(lower=0, upper=1).astype(int)


def _add_rejection_reason(df: pd.DataFrame, mask: pd.Series, reason: str) -> None:
    if not mask.any():
        return
    existing = df.loc[mask, "rejection_reason"].astype(str)
    df.loc[mask, "rejection_reason"] = np.where(existing == "", reason, existing + "|" + reason)


def _impute_group(group: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    g = group.sort_values("timestamp").copy()
    gap_minutes = g["timestamp"].diff().dt.total_seconds().div(60.0).fillna(0.0)
    segment_id = (gap_minutes > MAX_INTERPOLATION_GAP_MINUTES).cumsum()

    imputed_any = pd.Series(False, index=g.index)
    for col in numeric_cols:
        original_na = g[col].isna()
        filled = g[col].copy()
        for _, idx in g.groupby(segment_id).groups.items():
            segment = g.loc[idx, col]
            segment_filled = segment.interpolate(
                method="linear",
                limit=MAX_INTERPOLATION_STEPS,
                limit_direction="both",
            )
            filled.loc[idx] = segment_filled
        g[col] = filled
        imputed_any = imputed_any | (original_na & g[col].notna())

    g["is_imputed"] = imputed_any
    return g


def process_bronze_to_silver() -> Path:
    cfg = ensure_data_dirs()
    bronze_df = read_parquet_dir(cfg.bronze_dir)
    if bronze_df.empty:
        raise RuntimeError(f"No Bronze parquet files found in {cfg.bronze_dir}")

    expected_cols = {
        "timestamp",
        "apr_id",
        "sensor_id",
        "flow_lps",
        "pressure_bar",
        "tank_level_pct",
        "turbidity_ntu",
        "pump_on",
        "is_synthetic",
    }
    missing = expected_cols.difference(bronze_df.columns)
    if missing:
        raise ValueError(f"Missing expected columns in bronze data: {sorted(missing)}")

    df = bronze_df.copy()
    df["rejection_reason"] = ""
    input_rows = len(df)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["apr_id"] = df["apr_id"].fillna("").astype(str).str.strip()
    df["sensor_id"] = df["sensor_id"].fillna("").astype(str).str.strip()

    invalid_timestamp_mask = df["timestamp"].isna()
    missing_apr_mask = df["apr_id"].isin(["", "nan", "None"])
    missing_sensor_mask = df["sensor_id"].isin(["", "nan", "None"])

    _add_rejection_reason(df=df, mask=invalid_timestamp_mask, reason="invalid_timestamp")
    _add_rejection_reason(df=df, mask=missing_apr_mask, reason="missing_apr_id")
    _add_rejection_reason(df=df, mask=missing_sensor_mask, reason="missing_sensor_id")

    prefilter_rejected = df[df["rejection_reason"] != ""].copy()
    working = df[df["rejection_reason"] == ""].copy()

    numeric_cols = ["flow_lps", "pressure_bar", "tank_level_pct", "turbidity_ntu"]
    for col in numeric_cols:
        working[col] = pd.to_numeric(working[col], errors="coerce")
    working["pump_on"] = _coerce_pump_on(working["pump_on"])
    working["is_synthetic"] = working["is_synthetic"].fillna(False).astype(bool)

    duplicate_mask = working.duplicated(subset=["apr_id", "sensor_id", "timestamp"], keep="last")
    duplicate_rejected = working[duplicate_mask].copy()
    duplicate_rejected["rejection_reason"] = "duplicate_record_replaced"
    working = working[~duplicate_mask].copy()

    range_rules: dict[str, tuple[float, float]] = {
        "flow_lps": (0.0, 35.0),
        "pressure_bar": (0.0, 7.0),
        "tank_level_pct": (0.0, 100.0),
        "turbidity_ntu": (0.0, 20.0),
    }
    out_of_range_counts: dict[str, int] = {}
    for col, (low, high) in range_rules.items():
        invalid_mask = (working[col] < low) | (working[col] > high)
        count = int(invalid_mask.sum())
        out_of_range_counts[col] = count
        if count:
            LOGGER.info("Column %s has %d out-of-range values replaced with NaN", col, count)
            working.loc[invalid_mask, col] = np.nan

    groups: list[pd.DataFrame] = []
    for _, group in working.groupby(["apr_id", "sensor_id"], sort=False):
        groups.append(_impute_group(group=group, numeric_cols=numeric_cols))
    working = pd.concat(groups, ignore_index=False) if groups else pd.DataFrame(columns=working.columns)
    working = working.sort_values(["apr_id", "sensor_id", "timestamp"]).reset_index(drop=True)

    unresolved_mask = working[numeric_cols].isna().any(axis=1)
    unresolved_rejected = working[unresolved_mask].copy()
    unresolved_rejected["rejection_reason"] = "unresolved_missing_after_imputation"
    silver_df = working[~unresolved_mask].copy()

    silver_df["pressure_ok"] = silver_df["pressure_bar"].between(PRESSURE_MIN_BAR, PRESSURE_MAX_BAR)
    silver_df["turbidity_alert"] = silver_df["turbidity_ntu"] > TURBIDITY_ALERT_NTU
    silver_df["pump_on"] = silver_df["pump_on"].astype(bool)
    silver_df["is_imputed"] = silver_df["is_imputed"].fillna(False).astype(bool)

    silver_df = silver_df[
        [
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
            "is_synthetic",
            "is_imputed",
        ]
    ].copy()

    rejected_df = pd.concat(
        [prefilter_rejected, duplicate_rejected, unresolved_rejected],
        ignore_index=True,
        sort=False,
    )
    if not rejected_df.empty:
        rejected_df = rejected_df.sort_values("timestamp", na_position="last").reset_index(drop=True)
    if "is_imputed" in rejected_df.columns:
        rejected_df["is_imputed"] = rejected_df["is_imputed"].astype("boolean").fillna(False).astype(bool)

    write_parquet(df=silver_df, path=cfg.silver_file)
    write_parquet(df=rejected_df, path=cfg.silver_rejected_file)

    imputed_rows = int(silver_df["is_imputed"].sum()) if not silver_df.empty else 0
    rejected_rows = int(len(rejected_df))
    unresolved_rows = int(len(unresolved_rejected))
    silver_rows = int(len(silver_df))
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_bronze_dir": str(cfg.bronze_dir),
        "input_rows": int(input_rows),
        "silver_rows": silver_rows,
        "rejected_rows": rejected_rows,
        "rejection_rate_pct": round((rejected_rows / input_rows) * 100.0, 4) if input_rows else 0.0,
        "duplicates_removed": int(len(duplicate_rejected)),
        "unresolved_rows_after_imputation": unresolved_rows,
        "imputed_rows": imputed_rows,
        "imputed_pct_of_silver": round((imputed_rows / silver_rows) * 100.0, 4) if silver_rows else 0.0,
        "max_interpolation_gap_minutes": MAX_INTERPOLATION_GAP_MINUTES,
        "max_interpolation_steps": MAX_INTERPOLATION_STEPS,
        "invalid_timestamp_rows": int(invalid_timestamp_mask.sum()),
        "missing_apr_rows": int(missing_apr_mask.sum()),
        "missing_sensor_rows": int(missing_sensor_mask.sum()),
        "out_of_range_counts": out_of_range_counts,
    }
    cfg.silver_quality_report_file.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    LOGGER.info(
        "Silver transform completed (%d rows). Rejected=%d, Imputed=%d.",
        silver_rows,
        rejected_rows,
        imputed_rows,
    )
    return cfg.silver_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform Bronze telemetry to Silver data.")
    parser.parse_args()
    path = process_bronze_to_silver()
    print(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
