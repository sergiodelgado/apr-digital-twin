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

## Pump On, No Recovery

```powershell
python scripts/demo_workflow.py prepare --scenario pump_on_no_recovery --apr-id APR-001
```

Expected hydraulic signals:
- `HYDRAULIC_PUMP_ON_NO_RECOVERY`
- `possible_root_cause`: pump running but storage not recovering

## Abnormal Tank Drop

```powershell
python scripts/demo_workflow.py prepare --scenario abnormal_tank_drop --apr-id APR-001
```

Expected hydraulic signals:
- `HYDRAULIC_ABNORMAL_TANK_DROP_RATE`
- `possible_root_cause`: tank dropping faster than typical demand behavior

## Low Pressure With Normal Storage

```powershell
python scripts/demo_workflow.py prepare --scenario low_pressure_with_normal_storage --apr-id APR-001
```

Expected hydraulic signals:
- `HYDRAULIC_LOW_PRESSURE_WITH_NORMAL_STORAGE`
- `possible_root_cause`: distribution-side hydraulic losses with adequate storage

## Demand Spike With Storage Depletion

```powershell
python scripts/demo_workflow.py prepare --scenario demand_spike_with_storage_depletion --apr-id APR-001
```

Expected hydraulic signals:
- `HYDRAULIC_PROJECTED_DEPLETION_INSUFFICIENT_RECOVERY`
- `possible_root_cause`: outflow exceeds recovery capacity

## Noisy Or Erratic Tank Sensor

```powershell
python scripts/demo_workflow.py prepare --scenario noisy_or_erratic_tank_sensor --apr-id APR-001
```

Expected hydraulic signals:
- `HYDRAULIC_TANK_SENSOR_ERRATIC`
- `possible_root_cause`: tank level sensor appears noisy or erratic
