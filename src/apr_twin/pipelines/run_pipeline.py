from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.apr_twin.pipelines.bronze_to_silver import process_bronze_to_silver
from src.apr_twin.pipelines.silver_to_gold import process_silver_to_gold
from src.apr_twin.synthetic.generator import generate_bronze_telemetry

LOGGER = logging.getLogger(__name__)


def run_local_batch(days: int = 7, freq_minutes: int = 5, apr_id: str = "APR-001") -> dict[str, Path]:
    bronze_path = generate_bronze_telemetry(days=days, freq_minutes=freq_minutes, apr_id=apr_id)
    silver_path = process_bronze_to_silver()
    gold_path = process_silver_to_gold()
    output = {"bronze": Path(bronze_path), "silver": silver_path, "gold": gold_path}
    LOGGER.info("Local batch complete: %s", output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local APR batch pipeline.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--freq-minutes", type=int, default=5)
    parser.add_argument("--apr-id", type=str, default="APR-001")
    args = parser.parse_args()

    result = run_local_batch(days=args.days, freq_minutes=args.freq_minutes, apr_id=args.apr_id)
    for name, path in result.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

