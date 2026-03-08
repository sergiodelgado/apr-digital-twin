# Daily Health Check Prompt Template

Use this template when creating a recurring daily check for local MVP health.

## Prompt

Review the APR Digital Twin local MVP health using only current repository commands and data layers.  
Check whether Bronze, Silver, and Gold artifacts are present and recent; inspect API health semantics from local data; run a lightweight twin-state validation for `APR-001`; and summarize operational risks.

Provide output in this format:

1. `Snapshot`: timestamp, branch, and key environment assumptions.
2. `Data Layer Status`: Bronze/Silver/Gold file presence, freshness, and row-count notes.
3. `Twin Health`: current status, freshness, confidence, and reason codes.
4. `Risk Flags`: concrete issues with severity (`low`, `medium`, `high`).
5. `Recommended Next Actions`: short, executable follow-ups.

Constraints:

- Do not redesign architecture or add services.
- Stay consistent with the existing local MVP workflow.
