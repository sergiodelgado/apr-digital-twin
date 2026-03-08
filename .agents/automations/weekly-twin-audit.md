# Weekly Twin Audit Prompt Template

Use this template when creating a recurring weekly audit focused on twin behavior.

## Prompt

Run a weekly audit of APR Digital Twin rule behavior using the existing local scenario workflow.

For scenarios `normal`, `stale_data`, `low_pressure`, `high_turbidity`, and `projected_low_tank_level`:

- execute the scenario preparation flow
- capture twin output signals (`system_status`, `freshness_status`, `confidence_score`, `reason_codes`, `operational_recommendation`)
- compare observed behavior with expected outcome from current rule thresholds

Return:

1. `Scenario Matrix`: observed outputs per scenario.
2. `Behavior Assessment`: pass/fail per scenario with rationale.
3. `Trend Notes`: recurring issues vs previous audits.
4. `Action Plan`: prioritized fixes or test additions within current MVP boundaries.

Constraints:

- Preserve current architecture and command workflow.
- Keep all evidence local and reproducible.
