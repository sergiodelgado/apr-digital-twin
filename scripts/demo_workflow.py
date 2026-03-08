from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

try:
    from apr_twin.config import ensure_data_dirs
    from apr_twin.pipelines.bronze_to_silver import process_bronze_to_silver
    from apr_twin.pipelines.silver_to_gold import process_silver_to_gold
    from apr_twin.storage.parquet_io import read_parquet_file, write_parquet
    from apr_twin.synthetic.generator import generate_bronze_telemetry
    from apr_twin.twin.engine import compute_current_state
    from apr_twin.utils.logging_utils import configure_logging
except ModuleNotFoundError:
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))
    from apr_twin.config import ensure_data_dirs
    from apr_twin.pipelines.bronze_to_silver import process_bronze_to_silver
    from apr_twin.pipelines.silver_to_gold import process_silver_to_gold
    from apr_twin.storage.parquet_io import read_parquet_file, write_parquet
    from apr_twin.synthetic.generator import generate_bronze_telemetry
    from apr_twin.twin.engine import compute_current_state
    from apr_twin.utils.logging_utils import configure_logging

LOGGER = logging.getLogger(__name__)

SCENARIOS = (
    "normal",
    "stale_data",
    "low_pressure",
    "high_turbidity",
    "projected_low_tank_level",
)


def _clear_previous_outputs() -> None:
    cfg = ensure_data_dirs()
    deleted = 0
    for path in cfg.bronze_dir.glob("*.parquet"):
        path.unlink(missing_ok=True)
        deleted += 1
    for path in (
        cfg.silver_file,
        cfg.silver_rejected_file,
        cfg.silver_quality_report_file,
        cfg.gold_daily_file,
    ):
        path.unlink(missing_ok=True)
    LOGGER.info("Cleared previous demo outputs (removed %d bronze parquet files).", deleted)


def _nominalize_tail(df: pd.DataFrame, freq_minutes: int) -> pd.DataFrame:
    out = df.copy()
    points = min(len(out), max(24, int(180 / max(freq_minutes, 1))))
    if points == 0:
        return out
    tail_idx = out.index[-points:]

    out.loc[tail_idx, "pressure_bar"] = np.linspace(2.05, 2.25, points)
    out.loc[tail_idx, "tank_level_pct"] = np.linspace(64.0, 58.0, points)
    out.loc[tail_idx, "turbidity_ntu"] = np.linspace(0.34, 0.26, points)
    out.loc[tail_idx, "flow_lps"] = np.linspace(2.3, 2.7, points)
    out.loc[tail_idx, "pump_on"] = 0
    return out


def _apply_scenario(df: pd.DataFrame, scenario: str, freq_minutes: int, stale_minutes: int) -> pd.DataFrame:
    out = _nominalize_tail(df=df, freq_minutes=freq_minutes)
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")

    if scenario == "normal":
        return out

    if scenario == "stale_data":
        out["timestamp"] = out["timestamp"] - pd.Timedelta(minutes=max(stale_minutes, 61))
        return out

    points = min(len(out), max(12, int(90 / max(freq_minutes, 1))))
    if points == 0:
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
        projected_points = min(len(out), max(36, int(180 / max(freq_minutes, 1))))
        projected_idx = out.index[-projected_points:]
        out.loc[projected_idx, "tank_level_pct"] = np.linspace(40.0, 34.0, projected_points)
        out.loc[projected_idx, "pressure_bar"] = np.linspace(2.0, 2.1, projected_points)
        out.loc[projected_idx, "turbidity_ntu"] = np.linspace(0.34, 0.30, projected_points)
        out.loc[projected_idx, "flow_lps"] = np.linspace(3.4, 4.0, projected_points)
        out.loc[projected_idx, "pump_on"] = 0
        return out

    raise ValueError(f"Unsupported scenario: {scenario}")


def _generate(days: int, freq_minutes: int, apr_id: str, seed: int) -> Path:
    bronze_path = generate_bronze_telemetry(days=days, freq_minutes=freq_minutes, apr_id=apr_id, seed=seed)
    LOGGER.info("Generated telemetry file: %s", bronze_path)
    return Path(bronze_path)


def _run_pipeline() -> tuple[Path, Path]:
    silver_path = process_bronze_to_silver()
    gold_path = process_silver_to_gold()
    LOGGER.info("Pipeline complete. Silver=%s Gold=%s", silver_path, gold_path)
    return silver_path, gold_path


def _prepare_demo(
    *,
    scenario: str,
    days: int,
    freq_minutes: int,
    apr_id: str,
    seed: int,
    stale_minutes: int,
    clear_previous: bool,
) -> None:
    if clear_previous:
        _clear_previous_outputs()

    bronze_path = _generate(days=days, freq_minutes=freq_minutes, apr_id=apr_id, seed=seed)
    bronze_df = read_parquet_file(bronze_path)
    if bronze_df.empty:
        raise RuntimeError("Generated bronze dataset is empty.")

    scenario_df = _apply_scenario(
        df=bronze_df,
        scenario=scenario,
        freq_minutes=freq_minutes,
        stale_minutes=stale_minutes,
    )
    write_parquet(df=scenario_df, path=bronze_path)
    silver_path, gold_path = _run_pipeline()

    twin_state = compute_current_state(apr_id=apr_id)
    print("\nDemo data prepared.\n")
    print(f"Scenario:     {scenario}")
    print(f"Bronze file:  {bronze_path}")
    print(f"Silver file:  {silver_path}")
    print(f"Gold file:    {gold_path}")
    print(f"Twin status:  {twin_state.system_status}")
    print(f"Freshness:    {twin_state.freshness_status}")
    print(f"Reason codes: {', '.join(twin_state.reason_codes) if twin_state.reason_codes else 'none'}")
    print(f"Recommendation: {twin_state.operational_recommendation}")
    print("\nStart API:")
    print("python scripts/demo_workflow.py api --port 8000")
    print("\nStart dashboard:")
    print("python scripts/demo_workflow.py dashboard")


def _print_state(apr_id: str) -> None:
    state = compute_current_state(apr_id=apr_id)
    print(json.dumps(state.model_dump(mode="json"), indent=2))


def _run_api(port: int, reload_enabled: bool) -> int:
    command = [sys.executable, "-m", "uvicorn", "apr_twin.api.main:app", "--port", str(port)]
    if reload_enabled:
        command.append("--reload")
    return subprocess.call(command, cwd=str(REPO_ROOT))


def _run_dashboard(server_port: int) -> int:
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(REPO_ROOT / "src" / "apr_twin" / "dashboard" / "app.py"),
        "--server.port",
        str(server_port),
    ]
    return subprocess.call(command, cwd=str(REPO_ROOT))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="APR Digital Twin demo workflow helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    clear_cmd = sub.add_parser("clear", help="Delete local bronze/silver/gold artifacts for a clean demo run.")
    clear_cmd.set_defaults(handler=lambda args: _clear_previous_outputs())

    gen_cmd = sub.add_parser("generate", help="Generate synthetic telemetry in the bronze layer.")
    gen_cmd.add_argument("--days", type=int, default=7)
    gen_cmd.add_argument("--freq-minutes", type=int, default=5)
    gen_cmd.add_argument("--apr-id", type=str, default="APR-001")
    gen_cmd.add_argument("--seed", type=int, default=42)
    gen_cmd.set_defaults(
        handler=lambda args: print(
            _generate(days=args.days, freq_minutes=args.freq_minutes, apr_id=args.apr_id, seed=args.seed)
        )
    )

    pipe_cmd = sub.add_parser("pipeline", help="Run bronze -> silver -> gold pipeline.")
    pipe_cmd.set_defaults(handler=lambda args: _run_pipeline())

    prep_cmd = sub.add_parser("prepare", help="Generate telemetry, apply a demo scenario, and run pipeline.")
    prep_cmd.add_argument("--scenario", type=str, choices=SCENARIOS, default="normal")
    prep_cmd.add_argument("--days", type=int, default=7)
    prep_cmd.add_argument("--freq-minutes", type=int, default=5)
    prep_cmd.add_argument("--apr-id", type=str, default="APR-001")
    prep_cmd.add_argument("--seed", type=int, default=42)
    prep_cmd.add_argument("--stale-minutes", type=int, default=180)
    prep_cmd.add_argument(
        "--clear-previous",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Clear previous local outputs before preparing this scenario.",
    )
    prep_cmd.set_defaults(
        handler=lambda args: _prepare_demo(
            scenario=args.scenario,
            days=args.days,
            freq_minutes=args.freq_minutes,
            apr_id=args.apr_id,
            seed=args.seed,
            stale_minutes=args.stale_minutes,
            clear_previous=args.clear_previous,
        )
    )

    state_cmd = sub.add_parser("state", help="Print current twin state as JSON.")
    state_cmd.add_argument("--apr-id", type=str, default="APR-001")
    state_cmd.set_defaults(handler=lambda args: _print_state(apr_id=args.apr_id))

    api_cmd = sub.add_parser("api", help="Start FastAPI for demo.")
    api_cmd.add_argument("--port", type=int, default=8000)
    api_cmd.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable uvicorn reload.",
    )
    api_cmd.set_defaults(handler=lambda args: sys.exit(_run_api(port=args.port, reload_enabled=args.reload)))

    dashboard_cmd = sub.add_parser("dashboard", help="Start Streamlit dashboard for demo.")
    dashboard_cmd.add_argument("--port", type=int, default=8501)
    dashboard_cmd.set_defaults(handler=lambda args: sys.exit(_run_dashboard(server_port=args.port)))

    return parser


def main() -> None:
    configure_logging()
    parser = _build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
