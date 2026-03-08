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

- `README.md` rewritten to be presentation-ready with clear sections for project purpose, MVP architecture, demo workflow, repository structure, and `.agents` assets.

## [0.1.0] - 2026-03-08

### Initial

- Local APR Digital Twin MVP with synthetic telemetry generation, Bronze/Silver/Gold processing, twin state engine, FastAPI service, Streamlit dashboard, and baseline tests.
