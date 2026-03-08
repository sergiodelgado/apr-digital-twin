from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.apr_twin.config import ensure_data_dirs
from src.apr_twin.storage.parquet_io import write_parquet

LOGGER = logging.getLogger(__name__)


def _demand_profile_lps(timestamps: pd.DatetimeIndex, rng: np.random.Generator) -> np.ndarray:
    hour = timestamps.hour + (timestamps.minute / 60.0)
    morning_peak = np.exp(-((hour - 8.0) / 2.3) ** 2)
    evening_peak = np.exp(-((hour - 20.0) / 3.0) ** 2)
    base = 1.3 + (2.6 * morning_peak) + (3.4 * evening_peak)
    weekend_factor = np.where(timestamps.dayofweek >= 5, 0.9, 1.0)
    noise = rng.normal(loc=0.0, scale=0.2, size=len(timestamps))
    return np.clip((base * weekend_factor) + noise, 0.2, None)


def generate_bronze_telemetry(
    days: int = 7,
    freq_minutes: int = 5,
    apr_id: str = "APR-001",
    seed: int = 42,
) -> Path:
    cfg = ensure_data_dirs()
    rng = np.random.default_rng(seed)

    end_time = datetime.now().replace(second=0, microsecond=0)
    total_points = max(1, int((days * 24 * 60) / freq_minutes))
    timestamps = pd.date_range(end=end_time, periods=total_points, freq=f"{freq_minutes}min")
    step_seconds = freq_minutes * 60.0

    demand_lps = _demand_profile_lps(timestamps=timestamps, rng=rng)

    tank_capacity_m3 = 300.0
    tank_volume_m3 = 0.62 * tank_capacity_m3
    pump_on = False
    pump_rate_lps_nominal = 8.5

    leak_start = int(total_points * 0.55)
    leak_end = leak_start + int((180 / freq_minutes))
    turbidity_event_start = int(total_points * 0.35)
    turbidity_event_end = turbidity_event_start + int((240 / freq_minutes))

    rows: list[dict[str, object]] = []
    for i, ts in enumerate(timestamps):
        tank_level_pct = (tank_volume_m3 / tank_capacity_m3) * 100.0

        if tank_level_pct <= 35.0:
            pump_on = True
        elif tank_level_pct >= 92.0:
            pump_on = False

        leak_extra_lps = 1.7 if leak_start <= i <= leak_end else 0.0
        inflow_lps = (pump_rate_lps_nominal + rng.normal(0.0, 0.25)) if pump_on else 0.0
        outflow_lps = max(0.1, demand_lps[i] + leak_extra_lps)

        tank_volume_m3 += ((inflow_lps - outflow_lps) * step_seconds) / 1000.0
        tank_volume_m3 = float(np.clip(tank_volume_m3, 0.0, tank_capacity_m3))
        tank_level_pct = (tank_volume_m3 / tank_capacity_m3) * 100.0

        pressure_bar = (
            1.7
            + (1.1 * (tank_level_pct / 100.0))
            + (0.45 if pump_on else -0.15)
            - (0.30 if leak_extra_lps > 0 else 0.0)
            + rng.normal(0.0, 0.12)
        )
        pressure_bar = float(max(0.1, pressure_bar))

        turbidity_ntu = 0.18 + abs(rng.normal(0.12, 0.08))
        if turbidity_event_start <= i <= turbidity_event_end:
            decay = np.exp(-(i - turbidity_event_start) / 30.0)
            turbidity_ntu += 2.8 * decay

        flow_lps = float(outflow_lps + rng.normal(0.0, 0.1))

        # Inject limited sensor issues to exercise cleaning and validation logic.
        if rng.random() < 0.003:
            pressure_bar = 8.8
        if rng.random() < 0.003:
            tank_level_pct = -5.0
        if rng.random() < 0.004:
            flow_lps = np.nan
        if rng.random() < 0.004:
            turbidity_ntu = np.nan

        rows.append(
            {
                "timestamp": ts.to_pydatetime(),
                "apr_id": apr_id,
                "sensor_id": "station-main",
                "flow_lps": flow_lps,
                "pressure_bar": pressure_bar,
                "tank_level_pct": float(tank_level_pct),
                "turbidity_ntu": float(turbidity_ntu) if not pd.isna(turbidity_ntu) else np.nan,
                "pump_on": int(pump_on),
                "is_synthetic": True,
            }
        )

    df = pd.DataFrame(rows)
    output_path = cfg.bronze_dir / f"telemetry_raw_{datetime.now():%Y%m%d_%H%M%S}.parquet"
    write_parquet(df=df, path=output_path)
    LOGGER.info("Generated bronze telemetry at %s", output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic APR telemetry in Bronze layer.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--freq-minutes", type=int, default=5)
    parser.add_argument("--apr-id", type=str, default="APR-001")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    path = generate_bronze_telemetry(
        days=args.days,
        freq_minutes=args.freq_minutes,
        apr_id=args.apr_id,
        seed=args.seed,
    )
    print(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
