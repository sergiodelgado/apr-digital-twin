---
name: apr-pipeline-audit
description: Audit the Bronze to Silver to Gold local pipeline outputs for completeness, freshness, and quality signals. Use when asked to validate data artifacts, pipeline behavior, or basic operational health without redesigning the MVP.
---

# APR Pipeline Audit

## Audit Scope

- Bronze files in `data/bronze/`
- Silver outputs:
  - `data/silver/telemetry_silver.parquet`
  - `data/silver/rejected_records.parquet`
  - `data/silver/silver_quality_report.json`
- Gold output:
  - `data/gold/daily_kpis.parquet`

## Standard Procedure

1. Run `python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001` if data is missing.
2. Verify artifact presence and timestamps.
3. Check row counts and key fields in Silver and Gold.
4. Review rejection volume and quality report indicators.
5. Summarize risks and next actions.

## Guardrails

- Preserve current architecture and local execution model.
- Use existing scripts/modules; do not introduce new services.
- Keep findings action-oriented and auditable.
