# MVP Architecture (Local)

## Purpose

Describe the current APR Digital Twin MVP architecture as implemented in this repository, without introducing external services.

## Architecture Summary

The MVP runs entirely on local files and local processes:

1. Synthetic telemetry generation writes Bronze Parquet files.
2. Bronze to Silver pipeline validates, cleans, and standardizes telemetry.
3. Silver to Gold pipeline computes daily KPIs.
4. Twin engine computes current operational state from Silver and Gold.
5. FastAPI exposes telemetry, KPI, health, and twin endpoints.
6. Streamlit dashboard visualizes state and KPI trends from local files or API.

## Main Components

- Synthetic generator: `src/apr_twin/synthetic/generator.py`
- Pipeline orchestration: `src/apr_twin/pipelines/run_pipeline.py`
- Bronze to Silver transform: `src/apr_twin/pipelines/bronze_to_silver.py`
- Silver to Gold transform: `src/apr_twin/pipelines/silver_to_gold.py`
- Twin engine: `src/apr_twin/twin/engine.py`
- API service: `src/apr_twin/api/main.py`
- Dashboard UI: `src/apr_twin/dashboard/app.py`
- Demo helper script: `scripts/demo_workflow.py`
- Batch runner script: `scripts/run_mvp.py`

## Data Layers

- `data/bronze/`: raw synthetic telemetry files.
- `data/silver/telemetry_silver.parquet`: cleaned telemetry.
- `data/silver/rejected_records.parquet`: invalid/rejected telemetry.
- `data/silver/silver_quality_report.json`: quality summary.
- `data/gold/daily_kpis.parquet`: aggregated daily KPIs.

`APR_DATA_DIR` can override the default local `data/` folder.

## Operational Logic Notes

- Freshness thresholds: `FRESH <= 15 min`, `STALE <= 60 min`, otherwise `OUTDATED`.
- Core rule thresholds are configured in `src/apr_twin/config.py` (pressure, turbidity, tank level, interpolation limits).
- Twin output includes status, reason codes, confidence score, alerts, and recommendation.

## Out-of-Scope for This MVP

- External cloud data stores.
- Managed stream processing.
- Multi-tenant authentication/authorization.
- Event-driven microservices.
