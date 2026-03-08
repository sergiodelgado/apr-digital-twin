# Troubleshooting

## API Starts but Returns Empty Lists

- Cause: Silver/Gold files are missing or stale.
- Action: run `python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001`.

## Dashboard Loads but Shows No APR

- Cause: API endpoint mismatch or no processed data.
- Action:
  1. verify API URL is `http://127.0.0.1:8000`
  2. call `GET /available_aprs`
  3. rerun scenario preparation

## Twin State Returns `NO_DATA`

- Cause: no valid Silver telemetry for selected APR.
- Action:
  1. confirm APR exists via `GET /available_aprs`
  2. regenerate with `--apr-id APR-001`
  3. rerun Bronze to Silver and Silver to Gold

## Dependency/Import Errors

- Cause: environment not activated or package not installed in editable mode.
- Action:
  1. activate `.venv`
  2. run `python -m pip install -e .`
