from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src.apr_twin.config import ensure_data_dirs
from src.apr_twin.pipelines.bronze_to_silver import process_bronze_to_silver
from src.apr_twin.pipelines.silver_to_gold import process_silver_to_gold
from src.apr_twin.storage.parquet_io import read_parquet_file, write_parquet
from src.apr_twin.synthetic.generator import generate_bronze_telemetry
from src.apr_twin.twin.engine import compute_current_state


def _write_bronze(cfg_path: Path, rows: list[dict[str, object]]) -> None:
    df = pd.DataFrame(rows)
    df.to_parquet(cfg_path, index=False)


def test_end_to_end_pipeline_with_quality_outputs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APR_DATA_DIR", str(tmp_path / "data"))
    cfg = ensure_data_dirs()

    bronze_path = generate_bronze_telemetry(days=2, freq_minutes=5, apr_id="APR-TEST", seed=7)
    silver_path = process_bronze_to_silver()
    gold_path = process_silver_to_gold()

    assert Path(bronze_path).exists()
    assert silver_path.exists()
    assert gold_path.exists()
    assert cfg.silver_rejected_file.exists()
    assert cfg.silver_quality_report_file.exists()

    silver_df = read_parquet_file(cfg.silver_file)
    gold_df = read_parquet_file(cfg.gold_daily_file)

    assert not silver_df.empty
    assert not gold_df.empty
    assert {"pressure_ok", "turbidity_alert", "is_imputed"}.issubset(silver_df.columns)
    assert {
        "daily_volume_m3",
        "pressure_ok_ratio",
        "risk_level",
        "completeness_pct",
        "imputed_pct",
        "low_pressure_duration_minutes",
        "high_turbidity_duration_minutes",
    }.issubset(gold_df.columns)

    report = json.loads(cfg.silver_quality_report_file.read_text(encoding="utf-8"))
    assert report["input_rows"] >= report["silver_rows"]
    assert "out_of_range_counts" in report

    state = compute_current_state(apr_id="APR-TEST")
    assert state.system_status in {"OK", "WARNING", "CRITICAL"}
    assert state.current_pressure_bar is not None
    assert state.freshness_status in {"FRESH", "STALE", "OUTDATED", "NO_DATA"}


def test_multi_sensor_dedup_preserves_valid_rows(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APR_DATA_DIR", str(tmp_path / "data"))
    cfg = ensure_data_dirs()

    t0 = datetime(2026, 1, 1, 0, 0, 0)
    t5 = datetime(2026, 1, 1, 0, 5, 0)
    rows = [
        {
            "timestamp": t0,
            "apr_id": "APR-M",
            "sensor_id": "s1",
            "flow_lps": 2.0,
            "pressure_bar": 2.0,
            "tank_level_pct": 50.0,
            "turbidity_ntu": 0.5,
            "pump_on": 1,
            "is_synthetic": True,
        },
        {
            "timestamp": t0,
            "apr_id": "APR-M",
            "sensor_id": "s1",
            "flow_lps": 3.0,
            "pressure_bar": 2.2,
            "tank_level_pct": 50.0,
            "turbidity_ntu": 0.6,
            "pump_on": 1,
            "is_synthetic": True,
        },
        {
            "timestamp": t0,
            "apr_id": "APR-M",
            "sensor_id": "s2",
            "flow_lps": 4.0,
            "pressure_bar": 2.4,
            "tank_level_pct": 51.0,
            "turbidity_ntu": 0.7,
            "pump_on": 1,
            "is_synthetic": True,
        },
        {
            "timestamp": t5,
            "apr_id": "APR-M",
            "sensor_id": "s1",
            "flow_lps": 3.5,
            "pressure_bar": 2.3,
            "tank_level_pct": 52.0,
            "turbidity_ntu": 0.5,
            "pump_on": 1,
            "is_synthetic": True,
        },
        {
            "timestamp": None,
            "apr_id": "APR-M",
            "sensor_id": "s1",
            "flow_lps": 2.0,
            "pressure_bar": 2.0,
            "tank_level_pct": 50.0,
            "turbidity_ntu": 0.5,
            "pump_on": 1,
            "is_synthetic": True,
        },
    ]
    _write_bronze(cfg.bronze_dir / "custom.parquet", rows)

    process_bronze_to_silver()
    silver_df = read_parquet_file(cfg.silver_file)
    rejected_df = read_parquet_file(cfg.silver_rejected_file)

    same_ts = silver_df[silver_df["timestamp"] == pd.Timestamp(t0)]
    assert set(same_ts["sensor_id"].tolist()) == {"s1", "s2"}
    s1_row = same_ts[same_ts["sensor_id"] == "s1"].iloc[0]
    assert float(s1_row["flow_lps"]) == 3.0

    reasons = set(rejected_df["rejection_reason"].astype(str).tolist())
    assert "duplicate_record_replaced" in reasons
    assert any("invalid_timestamp" in r for r in reasons)


def test_gap_aware_interpolation_does_not_cross_long_outages(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APR_DATA_DIR", str(tmp_path / "data"))
    cfg = ensure_data_dirs()

    t0 = datetime(2026, 1, 1, 0, 0, 0)
    t120 = t0 + timedelta(minutes=120)
    t240 = t0 + timedelta(minutes=240)
    rows = [
        {
            "timestamp": t0,
            "apr_id": "APR-GAP",
            "sensor_id": "s1",
            "flow_lps": 2.0,
            "pressure_bar": 2.0,
            "tank_level_pct": 50.0,
            "turbidity_ntu": 0.4,
            "pump_on": 0,
            "is_synthetic": True,
        },
        {
            "timestamp": t120,
            "apr_id": "APR-GAP",
            "sensor_id": "s1",
            "flow_lps": 2.1,
            "pressure_bar": 8.8,
            "tank_level_pct": 49.0,
            "turbidity_ntu": 0.4,
            "pump_on": 0,
            "is_synthetic": True,
        },
        {
            "timestamp": t240,
            "apr_id": "APR-GAP",
            "sensor_id": "s1",
            "flow_lps": 1.9,
            "pressure_bar": 2.2,
            "tank_level_pct": 48.0,
            "turbidity_ntu": 0.4,
            "pump_on": 0,
            "is_synthetic": True,
        },
    ]
    _write_bronze(cfg.bronze_dir / "gap.parquet", rows)

    process_bronze_to_silver()
    silver_df = read_parquet_file(cfg.silver_file)
    rejected_df = read_parquet_file(cfg.silver_rejected_file)

    assert len(silver_df) == 2
    assert any(
        "unresolved_missing_after_imputation" in reason
        for reason in rejected_df["rejection_reason"].astype(str).tolist()
    )


def test_twin_freshness_degrades_state(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APR_DATA_DIR", str(tmp_path / "data"))
    cfg = ensure_data_dirs()

    stale_ts = datetime.now() - timedelta(hours=3)
    silver_df = pd.DataFrame(
        [
            {
                "timestamp": stale_ts,
                "apr_id": "APR-STALE",
                "sensor_id": "s1",
                "flow_lps": 2.0,
                "pressure_bar": 2.1,
                "tank_level_pct": 60.0,
                "turbidity_ntu": 0.5,
                "pump_on": False,
                "pressure_ok": True,
                "turbidity_alert": False,
                "is_synthetic": True,
                "is_imputed": False,
            }
        ]
    )
    write_parquet(silver_df, cfg.silver_file)

    state = compute_current_state(apr_id="APR-STALE")
    assert state.freshness_status == "OUTDATED"
    assert state.data_age_minutes is not None and state.data_age_minutes >= 120
    assert state.system_status == "CRITICAL"
    assert state.confidence <= 0.5
