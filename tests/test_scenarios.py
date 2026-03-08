from __future__ import annotations

from pathlib import Path

import pytest

from apr_twin.pipelines.bronze_to_silver import process_bronze_to_silver
from apr_twin.pipelines.silver_to_gold import process_silver_to_gold
from apr_twin.synthetic.generator import DEMO_SCENARIOS, generate_bronze_telemetry
from apr_twin.twin.engine import compute_current_state


def test_required_hydraulic_demo_scenarios_available() -> None:
    required = {
        "pump_on_no_recovery",
        "abnormal_tank_drop",
        "low_pressure_with_normal_storage",
        "demand_spike_with_storage_depletion",
        "noisy_or_erratic_tank_sensor",
    }
    assert required.issubset(set(DEMO_SCENARIOS))


@pytest.mark.parametrize(
    ("scenario", "expected_reason_code", "expected_root_cause_text"),
    [
        (
            "pump_on_no_recovery",
            "HYDRAULIC_PUMP_ON_NO_RECOVERY",
            "Pump is running but storage is not recovering as expected",
        ),
        (
            "abnormal_tank_drop",
            "HYDRAULIC_ABNORMAL_TANK_DROP_RATE",
            "Tank level is dropping faster than typical demand behavior",
        ),
        (
            "low_pressure_with_normal_storage",
            "HYDRAULIC_LOW_PRESSURE_WITH_NORMAL_STORAGE",
            "Distribution-side hydraulic losses are likely despite normal storage",
        ),
        (
            "demand_spike_with_storage_depletion",
            "HYDRAULIC_PROJECTED_DEPLETION_INSUFFICIENT_RECOVERY",
            "Net outflow is exceeding recovery capacity",
        ),
        (
            "noisy_or_erratic_tank_sensor",
            "HYDRAULIC_TANK_SENSOR_ERRATIC",
            "Tank level sensor appears noisy or erratic",
        ),
    ],
)
def test_hydraulic_enrichment_scenarios_trigger_expected_logic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    scenario: str,
    expected_reason_code: str,
    expected_root_cause_text: str,
) -> None:
    monkeypatch.setenv("APR_DATA_DIR", str(tmp_path / "data"))

    generate_bronze_telemetry(
        days=2,
        freq_minutes=5,
        apr_id="APR-SCEN",
        seed=17,
        scenario=scenario,
        stale_minutes=180,
    )
    process_bronze_to_silver()
    process_silver_to_gold()

    state = compute_current_state(apr_id="APR-SCEN")

    assert expected_reason_code in state.reason_codes
    assert state.possible_root_cause is not None
    assert expected_root_cause_text in state.possible_root_cause

