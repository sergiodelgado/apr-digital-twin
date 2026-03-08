# Demo Workflow

## Objective

Run a complete local APR digital twin demo using three terminals, with scenario switching to showcase operational insights.

## Prerequisites

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Terminal Plan

- Terminal A: data preparation and scenario switching.
- Terminal B: API.
- Terminal C: dashboard.

## 1) Prepare Demo Data (Terminal A)

```powershell
python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001 --days 7 --freq-minutes 5
```

This performs a clean local reset, telemetry generation, scenario shaping, and Bronze to Silver to Gold processing.

Hydraulic-focused scenarios available for `--scenario` include:

- `pump_on_no_recovery`
- `abnormal_tank_drop`
- `low_pressure_with_normal_storage`
- `demand_spike_with_storage_depletion`
- `noisy_or_erratic_tank_sensor`

## 2) Start API (Terminal B)

```powershell
python scripts/demo_workflow.py api --port 8000
```

Equivalent:

```powershell
uvicorn apr_twin.api.main:app --reload --port 8000
```

## 3) Start Dashboard (Terminal C)

```powershell
python scripts/demo_workflow.py dashboard --port 8501
```

Equivalent:

```powershell
python -m streamlit run src/apr_twin/dashboard/app.py
```

Open `http://localhost:8501`.

## 4) Dashboard Settings for Storytelling

- Data access mode: `API`
- API endpoint: `http://127.0.0.1:8000`
- APR in operation: `APR-001`
