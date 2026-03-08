from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)


def read_parquet_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        LOGGER.info("Parquet file not found: %s", path)
        return pd.DataFrame()
    return pd.read_parquet(path)


def read_parquet_dir(directory: Path) -> pd.DataFrame:
    files = sorted(directory.glob("*.parquet"))
    if not files:
        LOGGER.info("No parquet files found in %s", directory)
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for file_path in files:
        try:
            frames.append(pd.read_parquet(file_path))
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Skipping unreadable parquet file %s: %s", file_path, exc)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def write_parquet(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    LOGGER.info("Wrote parquet file: %s (%d rows)", path, len(df))
    return path

