from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from apr_twin.config import ensure_data_dirs
from apr_twin.storage.parquet_io import write_parquet

LOGGER = logging.getLogger(__name__)

DEMO_SCENARIOS: tuple[str, ...] = (
    "normal",
    "stale_data",
    "low_pressure",
    "high_turbidity",
    "projected_low_tank_level",
    "pump_on_no_recovery",
    "abnormal_tank_drop",
    "low_pressure_with_normal_storage",
    "demand_spike_with_storage_depletion",
    "noisy_or_erratic_tank_sensor",
)


def _demand_profile_lps(timestamps: pd.DatetimeIndex, rng: np.random.Generator) -> np.ndarray:
    hour = timestamps.hour + (timestamps.minute / 60.0)
    morning_peak = np.exp(-((hour - 8.0) / 2.3) ** 2)
    evening_peak = np.exp(-((hour - 20.0) / 3.0) ** 2)
    base = 1.3 + (2.6 * morning_peak) + (3.4 * evening_peak)
    weekend_factor = np.where(timestamps.dayofweek >= 5, 0.9, 1.0)
    noise = rng.normal(loc=0.0, scale=0.2, size=len(timestamps))
    return np.clip((base * weekend_factor) + noise, 0.2, None)


def _tail_points(total_rows: int, freq_minutes: int, window_minutes: int, min_points: int) -> int:
    if total_rows <= 0:
        return 0
    points = max(min_points, int(window_minutes / max(freq_minutes, 1)))
    return min(total_rows, points)


def _nominalize_tail(df: pd.DataFrame, freq_minutes: int) -> pd.DataFrame:
    out = df.copy()
    points = _tail_points(total_rows=len(out), freq_minutes=freq_minutes, window_minutes=180, min_points=24)
    if points <= 0:
        return out
    tail_idx = out.index[-points:]

    out.loc[tail_idx, "pressure_bar"] = np.linspace(2.05, 2.25, points)
    out.loc[tail_idx, "tank_level_pct"] = np.linspace(64.0, 58.0, points)
    out.loc[tail_idx, "turbidity_ntu"] = np.linspace(0.34, 0.26, points)
    out.loc[tail_idx, "flow_lps"] = np.linspace(2.3, 2.7, points)
    out.loc[tail_idx, "pump_on"] = 0
    return out


def apply_synthetic_scenario(
    df: pd.DataFrame,
    *,
    scenario: str,
    freq_minutes: int,
    stale_minutes: int = 180,
) -> pd.DataFrame:
    if scenario not in DEMO_SCENARIOS:
        raise ValueError(f"Unsupported scenario: {scenario}")

    out = _nominalize_tail(df=df, freq_minutes=freq_minutes)
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")

    if scenario == "normal":
        return out

    if scenario == "stale_data":
        out["timestamp"] = out["timestamp"] - pd.Timedelta(minutes=max(stale_minutes, 61))
        return out

    # Keep enough shaped points so the 2h hydraulic window is fully scenario-controlled.
    points = _tail_points(total_rows=len(out), freq_minutes=freq_minutes, window_minutes=150, min_points=26)
    if points <= 0:
        return out
    tail_idx = out.index[-points:]

    if scenario == "low_pressure":
        out.loc[tail_idx, "pressure_bar"] = np.linspace(1.35, 1.12, points)
        out.loc[tail_idx, "tank_level_pct"] = np.linspace(57.0, 54.0, points)
        out.loc[tail_idx, "turbidity_ntu"] = np.linspace(0.38, 0.32, points)
        out.loc[tail_idx, "pump_on"] = 1
        return out

    if scenario == "high_turbidity":
        out.loc[tail_idx, "pressure_bar"] = np.linspace(2.10, 2.22, points)
        out.loc[tail_idx, "tank_level_pct"] = np.linspace(58.0, 55.0, points)
        out.loc[tail_idx, "turbidity_ntu"] = np.linspace(2.4, 3.6, points)
        out.loc[tail_idx, "pump_on"] = 1
        return out

    if scenario == "projected_low_tank_level":
        projected_points = _tail_points(total_rows=len(out), freq_minutes=freq_minutes, window_minutes=180, min_points=36)
        projected_idx = out.index[-projected_points:]
        out.loc[projected_idx, "tank_level_pct"] = np.linspace(40.0, 34.0, projected_points)
        out.loc[projected_idx, "pressure_bar"] = np.linspace(2.0, 2.1, projected_points)
        out.loc[projected_idx, "turbidity_ntu"] = np.linspace(0.34, 0.30, projected_points)
        out.loc[projected_idx, "flow_lps"] = np.linspace(3.4, 4.0, projected_points)
        out.loc[projected_idx, "pump_on"] = 0
        return out

    if scenario == "pump_on_no_recovery":
        out.loc[tail_idx, "tank_level_pct"] = np.linspace(62.0, 60.0, points)
        out.loc[tail_idx, "pressure_bar"] = np.linspace(2.15, 2.25, points)
        out.loc[tail_idx, "turbidity_ntu"] = np.linspace(0.30, 0.28, points)
        out.loc[tail_idx, "flow_lps"] = np.linspace(3.2, 3.8, points)
        out.loc[tail_idx, "pump_on"] = 1
        return out

    if scenario == "abnormal_tank_drop":
        out.loc[tail_idx, "tank_level_pct"] = np.linspace(78.0, 66.0, points)
        out.loc[tail_idx, "pressure_bar"] = np.linspace(2.25, 2.10, points)
        out.loc[tail_idx, "turbidity_ntu"] = np.linspace(0.29, 0.31, points)
        out.loc[tail_idx, "flow_lps"] = np.linspace(3.7, 5.2, points)
        out.loc[tail_idx, "pump_on"] = 0
        return out

    if scenario == "low_pressure_with_normal_storage":
        out.loc[tail_idx, "tank_level_pct"] = np.linspace(62.0, 61.0, points)
        out.loc[tail_idx, "pressure_bar"] = np.linspace(1.30, 1.18, points)
        out.loc[tail_idx, "turbidity_ntu"] = np.linspace(0.32, 0.30, points)
        out.loc[tail_idx, "flow_lps"] = np.linspace(2.9, 3.2, points)
        out.loc[tail_idx, "pump_on"] = 0
        return out

    if scenario == "demand_spike_with_storage_depletion":
        out.loc[tail_idx, "tank_level_pct"] = np.linspace(33.5, 31.0, points)
        out.loc[tail_idx, "pressure_bar"] = np.linspace(1.95, 1.80, points)
        out.loc[tail_idx, "turbidity_ntu"] = np.linspace(0.33, 0.31, points)
        out.loc[tail_idx, "flow_lps"] = np.linspace(4.8, 6.2, points)
        pump_profile = np.ones(points, dtype=int)
        off_from = int(points * 0.75)
        pump_profile[off_from:] = 0
        out.loc[tail_idx, "pump_on"] = pump_profile
        return out

    if scenario == "noisy_or_erratic_tank_sensor":
        err_points = _tail_points(total_rows=len(out), freq_minutes=freq_minutes, window_minutes=125, min_points=25)
        err_idx = out.index[-err_points:]
        base = np.full(err_points, 55.0)
        oscillation = 6.0 * np.sin(np.linspace(0.0, 8.0 * np.pi, err_points))
        out.loc[err_idx, "tank_level_pct"] = np.clip(base + oscillation, 35.0, 85.0)
        out.loc[err_idx, "pressure_bar"] = np.linspace(2.15, 2.08, err_points)
        out.loc[err_idx, "turbidity_ntu"] = np.linspace(0.30, 0.34, err_points)
        out.loc[err_idx, "flow_lps"] = np.linspace(2.6, 2.9, err_points)
        out.loc[err_idx, "pump_on"] = 0
        return out

    raise ValueError(f"Unsupported scenario: {scenario}")


def generate_bronze_telemetry(
    days: int = 7,
    freq_minutes: int = 5,
    apr_id: str = "APR-001",
    seed: int = 42,
    scenario: str | None = None,
    stale_minutes: int = 180,
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
    if scenario is not None:
        df = apply_synthetic_scenario(
            df=df,
            scenario=scenario,
            freq_minutes=freq_minutes,
            stale_minutes=stale_minutes,
        )
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
    parser.add_argument("--scenario", type=str, choices=DEMO_SCENARIOS, default=None)
    parser.add_argument("--stale-minutes", type=int, default=180)
    args = parser.parse_args()

    path = generate_bronze_telemetry(
        days=args.days,
        freq_minutes=args.freq_minutes,
        apr_id=args.apr_id,
        seed=args.seed,
        scenario=args.scenario,
        stale_minutes=args.stale_minutes,
    )
    print(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

