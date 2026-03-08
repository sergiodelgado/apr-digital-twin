from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.apr_twin.pipelines.run_pipeline import run_local_batch


def test_api_endpoints(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APR_DATA_DIR", str(tmp_path / "data"))
    run_local_batch(days=2, freq_minutes=5, apr_id="APR-API")

    from src.apr_twin.api.main import app

    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] in {"ok", "warning"}

    telemetry = client.get("/telemetry/recent", params={"limit": 50, "apr_id": "APR-API"})
    assert telemetry.status_code == 200
    telemetry_payload = telemetry.json()
    assert isinstance(telemetry_payload, list)
    assert len(telemetry_payload) > 0
    assert "batch_id" in telemetry_payload[0]
    assert "source_file" in telemetry_payload[0]
    assert "processed_at" in telemetry_payload[0]

    kpis = client.get("/kpis/daily", params={"days": 10, "apr_id": "APR-API"})
    assert kpis.status_code == 200
    kpis_payload = kpis.json()
    assert isinstance(kpis_payload, list)
    assert len(kpis_payload) > 0
    assert "completeness_pct" in kpis_payload[0]
    assert "imputed_pct" in kpis_payload[0]
    assert "low_pressure_duration_minutes" in kpis_payload[0]
    assert "high_turbidity_duration_minutes" in kpis_payload[0]
    assert "batch_id" in kpis_payload[0]
    assert "source_file" in kpis_payload[0]
    assert "processed_at" in kpis_payload[0]

    twin = client.get("/twin/state", params={"apr_id": "APR-API"})
    assert twin.status_code == 200
    twin_payload = twin.json()
    assert twin_payload["system_status"] in {"OK", "WARNING", "CRITICAL", "NO_DATA"}
    assert twin_payload["freshness_status"] in {"FRESH", "STALE", "OUTDATED", "NO_DATA"}
    assert "data_age_minutes" in twin_payload
