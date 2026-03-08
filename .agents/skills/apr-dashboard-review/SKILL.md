---
name: apr-dashboard-review
description: Review dashboard readiness for stakeholder demos using the current Streamlit app and API integration. Use when asked to validate dashboard behavior, data visibility, and presentation consistency in the local MVP.
---

# APR Dashboard Review

## Review Targets

- Dashboard app: `src/apr_twin/dashboard/app.py`
- API service: `src/apr_twin/api/main.py`
- Demo workflow helper: `scripts/demo_workflow.py`

## Review Workflow

1. Prepare scenario data with `demo_workflow.py`.
2. Run API and dashboard on default ports.
3. Validate dashboard can read data in API mode.
4. Validate key screens for APR selection, twin state visibility, and KPI trends.
5. Record any reproducible UX or data consistency issues.

## Required Reporting

- Include commands used.
- Include observed vs expected behavior.
- Include severity and reproducibility notes.
- Keep recommendations within current MVP architecture.
