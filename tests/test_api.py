from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from apr_twin.pipelines.run_pipeline import run_local_batch


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_api_endpoints(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APR_DATA_DIR", str(tmp_path / "data"))
    run_local_batch(days=2, freq_minutes=5, apr_id="APR-API")

    from apr_twin.api.main import app

    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] in {"ok", "warning"}

    aprs = client.get("/available_aprs")
    assert aprs.status_code == 200
    aprs_payload = aprs.json()
    assert isinstance(aprs_payload, list)
    assert len(aprs_payload) >= 1
    assert any(str(row.get("apr_id")) == "APR-API" for row in aprs_payload)
    first_apr = aprs_payload[0]
    assert "apr_id" in first_apr
    assert "telemetry_records" in first_apr
    assert "kpi_records" in first_apr
    assert "first_telemetry_timestamp" in first_apr
    assert "last_telemetry_timestamp" in first_apr

    aprs_legacy = client.get("/aprs/available")
    assert aprs_legacy.status_code == 200
    assert aprs_legacy.json() == aprs_payload

    telemetry = client.get("/telemetry/recent", params={"limit": 5000, "apr_id": "APR-API"})
    assert telemetry.status_code == 200
    telemetry_payload = telemetry.json()
    assert isinstance(telemetry_payload, list)
    assert len(telemetry_payload) > 0
    assert "batch_id" in telemetry_payload[0]
    assert "source_file" in telemetry_payload[0]
    assert "processed_at" in telemetry_payload[0]

    start_ts = telemetry_payload[len(telemetry_payload) // 4]["timestamp"]
    end_ts = telemetry_payload[(len(telemetry_payload) * 3) // 4]["timestamp"]
    telemetry_filtered = client.get(
        "/telemetry/recent",
        params={"limit": 5000, "apr_id": "APR-API", "start": start_ts, "end": end_ts},
    )
    assert telemetry_filtered.status_code == 200
    telemetry_filtered_payload = telemetry_filtered.json()
    assert len(telemetry_filtered_payload) > 0
    start_dt = _parse_timestamp(start_ts)
    end_dt = _parse_timestamp(end_ts)
    for row in telemetry_filtered_payload:
        row_ts = _parse_timestamp(row["timestamp"])
        assert start_dt <= row_ts <= end_dt

    telemetry_invalid = client.get(
        "/telemetry/recent",
        params={"limit": 10, "apr_id": "APR-API", "start": end_ts, "end": start_ts},
    )
    assert telemetry_invalid.status_code == 400

    kpis = client.get("/kpis/daily", params={"days": 365, "apr_id": "APR-API"})
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

    start_day = kpis_payload[0]["date"]
    end_day = kpis_payload[-1]["date"]
    kpis_filtered = client.get(
        "/kpis/daily",
        params={"apr_id": "APR-API", "start": start_day, "end": end_day},
    )
    assert kpis_filtered.status_code == 200
    kpis_filtered_payload = kpis_filtered.json()
    assert len(kpis_filtered_payload) > 0
    for row in kpis_filtered_payload:
        assert start_day <= row["date"] <= end_day

    kpis_invalid = client.get(
        "/kpis/daily",
        params={"apr_id": "APR-API", "start": end_day, "end": start_day},
    )
    assert kpis_invalid.status_code == 400

    twin = client.get("/twin/state", params={"apr_id": "APR-API"})
    assert twin.status_code == 200
    twin_payload = twin.json()
    assert twin_payload["system_status"] in {"OK", "WARNING", "CRITICAL", "NO_DATA"}
    assert twin_payload["freshness_status"] in {"FRESH", "STALE", "OUTDATED", "NO_DATA"}
    assert twin_payload["confidence"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(twin_payload["confidence_score"], float)
    assert 0.0 <= twin_payload["confidence_score"] <= 1.0
    assert "reason_codes" in twin_payload
    assert isinstance(twin_payload["reason_codes"], list)
    assert "projected_tank_level_2h_pct" in twin_payload
    assert "operational_recommendation" in twin_payload
    assert "data_age_minutes" in twin_payload

