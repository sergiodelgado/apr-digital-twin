---
name: apr-demo-run
description: Run or reset the local APR Digital Twin demo workflow using existing repository commands. Use when asked to prepare scenarios, start API/dashboard processes, or execute a complete demo sequence for presentation.
---

# APR Demo Run

## Use Existing Entry Points

- Use `python scripts/demo_workflow.py prepare` for scenario setup.
- Use `python scripts/demo_workflow.py api` to run FastAPI.
- Use `python scripts/demo_workflow.py dashboard` to run Streamlit.
- Keep demo execution local and file-based.

## Standard Demo Sequence

1. Activate environment and dependencies.
2. Prepare scenario: `normal` unless a specific scenario is requested.
3. Start API on port `8000`.
4. Start dashboard on port `8501`.
5. Confirm `GET /health` and `GET /twin/state?apr_id=APR-001`.

## Scenario Commands

- `normal`
- `stale_data`
- `low_pressure`
- `high_turbidity`
- `projected_low_tank_level`

Use `python scripts/demo_workflow.py prepare --scenario <name> --apr-id APR-001`.

## Output Expectations

- Report commands executed.
- Report expected status/reason-code behavior per scenario.
- Do not modify architecture, service boundaries, or storage model.
