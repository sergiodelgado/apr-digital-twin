# Data Flow

## End-to-End Flow

1. `python -m apr_twin.synthetic.generator` produces telemetry into `data/bronze/`.
2. `python -m apr_twin.pipelines.bronze_to_silver` creates:
   - `data/silver/telemetry_silver.parquet`
   - `data/silver/rejected_records.parquet`
   - `data/silver/silver_quality_report.json`
3. `python -m apr_twin.pipelines.silver_to_gold` creates:
   - `data/gold/daily_kpis.parquet`
4. `apr_twin.twin.engine.compute_current_state` reads Silver/Gold to output operational state.
5. API and dashboard consume the same local datasets (directly or through API endpoints).

## API Endpoints Used in Demo

- `GET /health`
- `GET /available_aprs` and `GET /aprs/available`
- `GET /telemetry/recent`
- `GET /kpis/daily`
- `GET /twin/state`

## MVP Guardrail

All flow steps must remain executable from this repository using local Python processes and local Parquet storage.
