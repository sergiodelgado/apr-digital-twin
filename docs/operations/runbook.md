# Operations Runbook

## Daily Startup

1. Activate virtual environment.
2. Ensure dependencies are installed (`python -m pip install -e .`).
3. Prepare a scenario using `scripts/demo_workflow.py prepare`.
4. Start API and dashboard.

## Quick Health Checks

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "http://127.0.0.1:8000/twin/state?apr_id=APR-001"
```

## Local Batch Execution

```powershell
python scripts/run_mvp.py --days 7 --freq-minutes 5 --apr-id APR-001
```

## Tests

```powershell
python -m pytest -q
```

## Data Directory Override

```powershell
$env:APR_DATA_DIR = "C:\temp\apr-data"
```

Use this when separating demo artifacts from repository-local data.
