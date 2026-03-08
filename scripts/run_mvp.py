from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

try:
    from apr_twin.pipelines.run_pipeline import run_local_batch
    from apr_twin.twin.engine import compute_current_state
    from apr_twin.utils.logging_utils import configure_logging
except ModuleNotFoundError:
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))
    from apr_twin.pipelines.run_pipeline import run_local_batch
    from apr_twin.twin.engine import compute_current_state
    from apr_twin.utils.logging_utils import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local APR MVP batch flow.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--freq-minutes", type=int, default=5)
    parser.add_argument("--apr-id", type=str, default="APR-001")
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting local APR MVP batch flow...")

    outputs = run_local_batch(days=args.days, freq_minutes=args.freq_minutes, apr_id=args.apr_id)
    twin_state = compute_current_state(apr_id=args.apr_id)

    print("\nBatch flow completed.\n")
    print(f"Bronze file: {outputs['bronze']}")
    print(f"Silver file: {outputs['silver']}")
    print(f"Gold file:   {outputs['gold']}")
    print(f"Twin state:  {twin_state.system_status} | alerts={len(twin_state.active_alerts)}")

    print("\nStart API (separate process):")
    print("uvicorn apr_twin.api.main:app --reload --port 8000")
    print("\nStart Dashboard (separate process):")
    print("python -m streamlit run src/apr_twin/dashboard/app.py")


if __name__ == "__main__":
    main()

