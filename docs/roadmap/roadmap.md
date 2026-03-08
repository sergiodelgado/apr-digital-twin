# MVP Roadmap

This roadmap preserves the current local architecture (Parquet layers + Python services) and avoids introducing new infrastructure.

## Near-Term

- Harden data quality metrics in Silver quality report.
- Expand scenario library for richer demo narratives.
- Add test coverage for edge-case telemetry gaps and APR selection behavior.
- Improve dashboard presentation polish for stakeholder demos.

## Mid-Term

- Document API contract examples with sample payloads for all primary endpoints.
- Add benchmark scripts for pipeline runtime and data volume scaling checks.
- Standardize runbooks for demo day setup and reset procedures.

## Long-Term (Still Local MVP Compatible)

- Increase modularity of scenario generation while keeping single-repo execution.
- Add richer twin explainability views using existing reason codes/confidence outputs.
