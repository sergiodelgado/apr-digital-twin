# APR Digital Twin MVP (Local)

Local MVP for a digital twin platform for rural drinking water systems (APR).
Everything runs in this repository using local Parquet files and the existing `apr_twin` package modules.

## MVP architecture (local only)

- Synthetic telemetry generator -> `data/bronze/`
- Bronze -> Silver data cleaning/validation pipeline
- Silver -> Gold daily KPI pipeline
- Twin state engine (`apr_twin.twin.engine`)
- FastAPI service (`apr_twin.api.main`)
- Streamlit dashboard (`apr_twin.dashboard.app`)

## Project structure

```text
data/
  bronze/
  silver/
  gold/
scripts/
  run_mvp.py
  demo_workflow.py
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

## 1) Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## 2) Full local demo (step-by-step)

Use 3 terminals:

- Terminal A: data preparation / scenario switching
- Terminal B: API
- Terminal C: dashboard

### Terminal A - prepare demo data

Recommended first run:

```powershell
python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001 --days 7 --freq-minutes 5
```

This command will:

1. clear previous local artifacts (bronze/silver/gold)
2. generate synthetic telemetry
3. apply the selected demo scenario
4. run Bronze -> Silver -> Gold pipeline
5. print the resulting twin status/reason codes/recommendation

### Terminal B - start API

```powershell
python scripts/demo_workflow.py api --port 8000
```

Equivalent direct command:

```powershell
uvicorn apr_twin.api.main:app --reload --port 8000
```

### Terminal C - start dashboard

```powershell
python scripts/demo_workflow.py dashboard --port 8501
```

Equivalent direct command:

```powershell
python -m streamlit run src/apr_twin/dashboard/app.py
```

Open the dashboard at `http://localhost:8501`.
For demo storytelling with the API, in the sidebar choose:

- `Data access mode`: `API`
- `API endpoint`: `http://127.0.0.1:8000`
- `APR in operation`: `APR-001`

## 3) Demo scenario set

Run each command in Terminal A while API and dashboard stay up. After each run, refresh dashboard.

### Scenario: normal operation

```powershell
python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001
```

Expected story:

- Status tends to `OK`
- Freshness `FRESH`
- No active alerts or only minor residual warnings
- Recommendation is routine monitoring

### Scenario: stale data

```powershell
python scripts/demo_workflow.py prepare --scenario stale_data --apr-id APR-001 --stale-minutes 180
```

Expected story:

- Freshness `OUTDATED`
- Status escalates to `CRITICAL` because telemetry is old
- Recommendation focuses on restoring telemetry connectivity

### Scenario: low pressure

```powershell
python scripts/demo_workflow.py prepare --scenario low_pressure --apr-id APR-001
```

Expected story:

- `PRESSURE_LOW` reason code
- Warning/critical operational status depending on latest value
- Recommendation focuses on pressure stabilization actions

### Scenario: high turbidity

```powershell
python scripts/demo_workflow.py prepare --scenario high_turbidity --apr-id APR-001
```

Expected story:

- `TURBIDITY_HIGH` (and possibly `TURBIDITY_CRITICAL`) reason codes
- Water quality alert appears in API and dashboard
- Recommendation focuses on quality surveillance/incident response

### Scenario: projected low tank level

```powershell
python scripts/demo_workflow.py prepare --scenario projected_low_tank_level --apr-id APR-001
```

Expected story:

- `PROJECTED_TANK_LOW_2H` reason code appears
- Current tank may still be above low threshold, but 2-hour projection is risky
- Recommendation shifts to short-term replenishment planning

## 4) Manual workflow (without helper script)

Generate telemetry:

```powershell
python -m apr_twin.synthetic.generator --days 7 --freq-minutes 5 --apr-id APR-001
```

Run pipeline:

```powershell
python -m apr_twin.pipelines.bronze_to_silver
python -m apr_twin.pipelines.silver_to_gold
```

Or run end-to-end local batch:

```powershell
python scripts/run_mvp.py --days 7 --freq-minutes 5 --apr-id APR-001
```

## 5) Verify API quickly

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "http://127.0.0.1:8000/twin/state?apr_id=APR-001"
```

## 6) Run tests

```powershell
python -m pytest -q
```

## Optional data directory override

```powershell
$env:APR_DATA_DIR = "C:\temp\apr-data"
```
