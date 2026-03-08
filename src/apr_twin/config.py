from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PRESSURE_MIN_BAR: float = 1.5
PRESSURE_MAX_BAR: float = 4.5
TURBIDITY_ALERT_NTU: float = 2.0
TURBIDITY_CRITICAL_NTU: float = 5.0
TANK_LOW_PCT: float = 30.0
TANK_CRITICAL_PCT: float = 15.0
MAX_INTERPOLATION_GAP_MINUTES: float = 45.0
MAX_INTERPOLATION_STEPS: int = 6
FRESHNESS_FRESH_MAX_MINUTES: float = 15.0
FRESHNESS_STALE_MAX_MINUTES: float = 60.0
HYDRAULIC_TREND_WINDOW_HOURS: float = 2.0
PUMP_RECOVERY_MIN_TREND_PCT_PER_HOUR: float = 0.5
ABNORMAL_TANK_DROP_WARN_PCT_PER_HOUR: float = 4.0
ABNORMAL_TANK_DROP_CRITICAL_PCT_PER_HOUR: float = 8.0
NORMAL_STORAGE_MIN_PCT: float = 45.0
INSUFFICIENT_RECOVERY_MAX_TREND_PCT_PER_HOUR: float = 0.3


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    data_dir: Path
    bronze_dir: Path
    silver_dir: Path
    gold_dir: Path
    silver_file: Path
    gold_daily_file: Path
    silver_rejected_file: Path
    silver_quality_report_file: Path


def get_config() -> AppConfig:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = Path(os.environ.get("APR_DATA_DIR", str(project_root / "data"))).resolve()
    bronze_dir = data_dir / "bronze"
    silver_dir = data_dir / "silver"
    gold_dir = data_dir / "gold"

    return AppConfig(
        project_root=project_root,
        data_dir=data_dir,
        bronze_dir=bronze_dir,
        silver_dir=silver_dir,
        gold_dir=gold_dir,
        silver_file=silver_dir / "telemetry_silver.parquet",
        gold_daily_file=gold_dir / "daily_kpis.parquet",
        silver_rejected_file=silver_dir / "rejected_records.parquet",
        silver_quality_report_file=silver_dir / "silver_quality_report.json",
    )


def ensure_data_dirs() -> AppConfig:
    cfg = get_config()
    cfg.bronze_dir.mkdir(parents=True, exist_ok=True)
    cfg.silver_dir.mkdir(parents=True, exist_ok=True)
    cfg.gold_dir.mkdir(parents=True, exist_ok=True)
    return cfg
