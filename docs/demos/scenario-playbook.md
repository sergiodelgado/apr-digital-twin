# Scenario Playbook

Run each command in Terminal A while API and dashboard remain active. Refresh the dashboard after each run.

## Normal

```powershell
python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001
```

Expected: mostly `OK`, fresh telemetry, routine recommendation.

## Stale Data

```powershell
python scripts/demo_workflow.py prepare --scenario stale_data --apr-id APR-001 --stale-minutes 180
```

Expected: `OUTDATED` freshness, likely `CRITICAL`, connectivity-focused recommendation.

## Low Pressure

```powershell
python scripts/demo_workflow.py prepare --scenario low_pressure --apr-id APR-001
```

Expected: `PRESSURE_LOW` reason code and pressure stabilization guidance.

## High Turbidity

```powershell
python scripts/demo_workflow.py prepare --scenario high_turbidity --apr-id APR-001
```

Expected: turbidity reason codes and water quality-focused recommendation.

## Projected Low Tank Level

```powershell
python scripts/demo_workflow.py prepare --scenario projected_low_tank_level --apr-id APR-001
```

Expected: `PROJECTED_TANK_LOW_2H` with short-term replenishment planning recommendation.
