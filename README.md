# APR Digital Twin MVP (Local)

Local MVP for a digital twin platform for rural drinking water systems (APR).
Everything runs inside this repository with local Parquet files.

## What this MVP includes

- Synthetic telemetry generator into `data/bronze/`
- Bronze -> Silver cleaning and validation pipeline
- Silver -> Gold daily KPI pipeline
- Internal digital twin state engine (Python module)
- FastAPI service layer
- Streamlit dashboard
- Basic tests for pipeline and API

## Project structure

```text
data/
  bronze/
  silver/
  gold/
scripts/
  run_mvp.py
src/
  apr_twin/
    api/
    dashboard/
    pipelines/
    storage/
    synthetic/
    twin/
    utils/
tests/
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run local batch flow

```powershell
python scripts/run_mvp.py --days 7 --freq-minutes 5 --apr-id APR-001
```

This command generates telemetry and produces:

- Bronze: `data/bronze/*.parquet`
- Silver: `data/silver/telemetry_silver.parquet`
- Gold: `data/gold/daily_kpis.parquet`

## Start API

```powershell
python -m uvicorn apr_twin.api.main:app --reload --port 8000
```

## Start dashboard

```powershell
python -m streamlit run src/apr_twin/dashboard/app.py
```

## Run tests

```powershell
python -m pytest -q
```

## Optional data directory override

Set `APR_DATA_DIR` to use another local data folder:

```powershell
$env:APR_DATA_DIR = "C:\temp\apr-data"
```
