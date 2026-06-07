# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows semantic versioning principles for tagged releases.

## [Unreleased]

### Added

- Documentation structure under `docs/`:
  - `architecture/`
  - `demos/`
  - `operations/`
  - `roadmap/`
- Repository-local agent skills under `.agents/skills/`:
  - `apr-demo-run`
  - `apr-pipeline-audit`
  - `apr-dashboard-review`
  - `apr-twin-evaluation`
- Automation prompt templates under `.agents/automations/`:
  - `daily-health-check.md`
  - `repo-briefing.md`
  - `weekly-twin-audit.md`

### Changed

- `README.md` reorganized for public GitHub readiness with clearer overview, quick start, expected result, architecture, demo scenarios, documentation links, operations commands, tests, maturity, limitations, and roadmap sections.
- Demo execution flow clarified with local setup, scenario preparation, API startup, dashboard startup, and expected local URLs.
- Technical documentation links expanded to existing architecture, demo, operations, roadmap, changelog, and current technical state report documentation, including `docs/reports/estado-tecnico-actual.md`.
- Current MVP maturity and limitations clarified to avoid presenting the local synthetic-telemetry MVP as production-ready.

## [0.1.0] - 2026-03-08

### Initial

- Local APR Digital Twin MVP with synthetic telemetry generation, Bronze/Silver/Gold processing, twin state engine, FastAPI service, Streamlit dashboard, and baseline tests.
