---
name: apr-twin-evaluation
description: Evaluate digital twin state outputs, reason codes, freshness, confidence, and recommendations against demo scenarios. Use when asked to assess whether twin behavior matches current rule-based logic in the local MVP.
---

# APR Twin Evaluation

## Core Targets

- Twin engine logic: `src/apr_twin/twin/engine.py`
- Threshold config: `src/apr_twin/config.py`
- API twin endpoint: `GET /twin/state`

## Evaluation Flow

1. Run a baseline (`normal`) scenario.
2. Run each stress scenario (`stale_data`, `low_pressure`, `high_turbidity`, `projected_low_tank_level`).
3. Capture twin outputs: status, freshness, confidence score, reason codes, recommendation.
4. Compare observed outputs with expected rule behavior.
5. Summarize mismatches, potential root causes, and candidate follow-up tests.

## Guardrails

- Treat this as a rules-validation exercise, not an architecture redesign.
- Keep all execution local with existing scripts and data layers.
