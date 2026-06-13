from __future__ import annotations

from typing import Final, Sequence


class ReasonCode:
    APR_NOT_FOUND = "APR_NOT_FOUND_IN_SILVER"
    TELEMETRY_NO_DATA = "NO_DATA_SILVER"
    FRESHNESS_STALE = "FRESHNESS_STALE"
    FRESHNESS_OUTDATED = "FRESHNESS_OUTDATED"
    PRESSURE_LOW = "PRESSURE_LOW"
    PRESSURE_CRITICAL = "PRESSURE_CRITICAL"
    TANK_LOW = "TANK_LOW"
    TANK_CRITICAL = "TANK_CRITICAL"
    TANK_PROJECTED_LOW_2H = "PROJECTED_TANK_LOW_2H"
    TANK_PROJECTED_CRITICAL_2H = "PROJECTED_TANK_CRITICAL_2H"
    TURBIDITY_HIGH = "TURBIDITY_HIGH"
    TURBIDITY_CRITICAL = "TURBIDITY_CRITICAL"
    PUMP_NO_RECOVERY = "HYDRAULIC_PUMP_ON_NO_RECOVERY"
    TANK_DROP_WARN = "HYDRAULIC_ABNORMAL_TANK_DROP_RATE"
    TANK_DROP_CRITICAL = "HYDRAULIC_ABNORMAL_TANK_DROP_RATE_CRITICAL"
    PRESSURE_LOW_NORMAL_STORAGE = "HYDRAULIC_LOW_PRESSURE_WITH_NORMAL_STORAGE"
    DEPLETION_WEAK_RECOVERY = "HYDRAULIC_PROJECTED_DEPLETION_INSUFFICIENT_RECOVERY"
    TANK_SENSOR_ERRATIC = "HYDRAULIC_TANK_SENSOR_ERRATIC"
    HYDRAULIC_BALANCE_WATCH = "HYDRAULIC_BALANCE_WATCH"
    HYDRAULIC_BALANCE_INCONSISTENT = "HYDRAULIC_BALANCE_INCONSISTENT"
    HYDRAULIC_RISK_MEDIUM = "HYDRAULIC_RISK_MEDIUM"
    HYDRAULIC_RISK_HIGH = "HYDRAULIC_RISK_HIGH"
    HYDRAULIC_DATA_INSUFFICIENT = "HYDRAULIC_DATA_INSUFFICIENT"
    PRESSURE_COMPLIANCE_LOW = "PRESSURE_COMPLIANCE_BELOW_TARGET"
    KPI_RISK_MEDIUM = "DAILY_RISK_MEDIUM"
    KPI_RISK_HIGH = "DAILY_RISK_HIGH"
    DATA_QUALITY_WATCH = "DATA_COMPLETENESS_WATCH"
    DATA_QUALITY_AT_RISK = "DATA_COMPLETENESS_AT_RISK"
    DATA_QUALITY_UNKNOWN = "DATA_COMPLETENESS_UNKNOWN"


REASON_CODE_CATALOG: Final[tuple[str, ...]] = (
    ReasonCode.APR_NOT_FOUND,
    ReasonCode.TELEMETRY_NO_DATA,
    ReasonCode.FRESHNESS_STALE,
    ReasonCode.FRESHNESS_OUTDATED,
    ReasonCode.PRESSURE_LOW,
    ReasonCode.PRESSURE_CRITICAL,
    ReasonCode.TANK_LOW,
    ReasonCode.TANK_CRITICAL,
    ReasonCode.TANK_PROJECTED_LOW_2H,
    ReasonCode.TANK_PROJECTED_CRITICAL_2H,
    ReasonCode.TURBIDITY_HIGH,
    ReasonCode.TURBIDITY_CRITICAL,
    ReasonCode.PUMP_NO_RECOVERY,
    ReasonCode.TANK_DROP_WARN,
    ReasonCode.TANK_DROP_CRITICAL,
    ReasonCode.PRESSURE_LOW_NORMAL_STORAGE,
    ReasonCode.DEPLETION_WEAK_RECOVERY,
    ReasonCode.TANK_SENSOR_ERRATIC,
    ReasonCode.HYDRAULIC_BALANCE_WATCH,
    ReasonCode.HYDRAULIC_BALANCE_INCONSISTENT,
    ReasonCode.HYDRAULIC_RISK_MEDIUM,
    ReasonCode.HYDRAULIC_RISK_HIGH,
    ReasonCode.HYDRAULIC_DATA_INSUFFICIENT,
    ReasonCode.PRESSURE_COMPLIANCE_LOW,
    ReasonCode.KPI_RISK_MEDIUM,
    ReasonCode.KPI_RISK_HIGH,
    ReasonCode.DATA_QUALITY_WATCH,
    ReasonCode.DATA_QUALITY_AT_RISK,
    ReasonCode.DATA_QUALITY_UNKNOWN,
)


HYDRAULIC_MEDIUM_RISK_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        ReasonCode.PUMP_NO_RECOVERY,
        ReasonCode.TANK_DROP_WARN,
        ReasonCode.PRESSURE_LOW_NORMAL_STORAGE,
        ReasonCode.TANK_SENSOR_ERRATIC,
    }
)
HYDRAULIC_HIGH_RISK_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        ReasonCode.DEPLETION_WEAK_RECOVERY,
        ReasonCode.TANK_DROP_CRITICAL,
    }
)


class RootCause:
    APR_SELECTION_INVALID = "APR_SELECTION_INVALID"
    TELEMETRY_UNAVAILABLE = "TELEMETRY_UNAVAILABLE"
    TELEMETRY_STALE = "TELEMETRY_STALE"
    HYDRAULIC_DEPLETION_IMBALANCE = "HYDRAULIC_DEPLETION_IMBALANCE"
    HYDRAULIC_RECOVERY_FAILURE = "HYDRAULIC_RECOVERY_FAILURE"
    HYDRAULIC_DISTRIBUTION_LOSS = "HYDRAULIC_DISTRIBUTION_LOSS"
    HYDRAULIC_OBSERVABILITY_GAP = "HYDRAULIC_OBSERVABILITY_GAP"
    SENSOR_INSTABILITY = "SENSOR_INSTABILITY"
    STORAGE_DEPLETION_RISK = "STORAGE_DEPLETION_RISK"
    PRESSURE_DEGRADATION = "PRESSURE_DEGRADATION"
    WATER_QUALITY_DEGRADATION = "WATER_QUALITY_DEGRADATION"
    DATA_QUALITY_DEGRADATION = "DATA_QUALITY_DEGRADATION"
    KPI_RISK_SIGNAL = "KPI_RISK_SIGNAL"
    NORMAL_OPERATION = "NORMAL_OPERATION"


class RecommendationText:
    DATA_UNAVAILABLE = "Validate data availability before issuing operational decisions."
    APR_NOT_FOUND = "Select an APR with telemetry coverage in the current Silver dataset."
    TELEMETRY_OUTDATED = (
        "Validate telemetry connectivity and operate with field confirmation until live data recovers."
    )
    PROJECTED_DEPLETION = (
        "Projected depletion with weak recovery trend: verify pump output, check leakage/losses, "
        "and initiate near-term refill control."
    )
    PUMP_NO_RECOVERY = (
        "Pump is active but tank is not recovering: inspect pump discharge, valve positions, "
        "and potential network leakage."
    )
    DISTRIBUTION_HYDRAULICS = (
        "Low pressure with normal storage points to distribution hydraulics; inspect valves, PRVs, "
        "and line losses."
    )
    TANK_SENSOR_ERRATIC = (
        "Erratic tank signal detected: validate level sensor health before acting on storage trend alarms."
    )
    TANK_DROP_CRITICAL = (
        "Critical tank drop rate detected: investigate abnormal demand/leaks and stabilize storage immediately."
    )
    TANK_DROP_WARN = (
        "Tank is dropping faster than expected: increase surveillance and verify abnormal consumption patterns."
    )
    PRESSURE_CRITICAL = "Escalate immediately for critical low pressure and stabilize distribution."
    PRESSURE_LOW = "Investigate pressure losses and adjust pumping or valve operations."
    TANK_CRITICAL = "Prioritize immediate refill actions to avoid service interruption risk."
    TANK_LOW = "Prepare short-term replenishment and monitor tank level more frequently."
    TURBIDITY_CRITICAL = "Activate water quality incident response and verify treatment performance."
    TURBIDITY_HIGH = "Increase water quality surveillance and inspect treatment conditions."
    DATA_QUALITY_AT_RISK = (
        "Validate sensor data quality before relying on automated operational decisions."
    )
    DATA_QUALITY_WATCH = "Review data quality trends and confirm telemetry consistency during shifts."
    DATA_QUALITY_UNKNOWN = "Confirm daily KPI completeness before using this state for planning decisions."
    TELEMETRY_STALE = "Keep operations stable and prioritize telemetry refresh in the next cycle."
    NORMAL_OPERATION = (
        "Continue normal operation with routine monitoring of pressure, tank level, and turbidity."
    )


ENGINE_RECOMMENDATION_CATALOG: Final[tuple[str, ...]] = (
    RecommendationText.DATA_UNAVAILABLE,
    RecommendationText.APR_NOT_FOUND,
    RecommendationText.TELEMETRY_OUTDATED,
    RecommendationText.PROJECTED_DEPLETION,
    RecommendationText.PUMP_NO_RECOVERY,
    RecommendationText.DISTRIBUTION_HYDRAULICS,
    RecommendationText.TANK_SENSOR_ERRATIC,
    RecommendationText.TANK_DROP_CRITICAL,
    RecommendationText.TANK_DROP_WARN,
    RecommendationText.PRESSURE_CRITICAL,
    RecommendationText.PRESSURE_LOW,
    RecommendationText.TANK_CRITICAL,
    RecommendationText.TANK_LOW,
    RecommendationText.TURBIDITY_CRITICAL,
    RecommendationText.TURBIDITY_HIGH,
    RecommendationText.DATA_QUALITY_AT_RISK,
    RecommendationText.DATA_QUALITY_WATCH,
    RecommendationText.DATA_QUALITY_UNKNOWN,
    RecommendationText.TELEMETRY_STALE,
    RecommendationText.NORMAL_OPERATION,
)


ROOT_CAUSE_RULES: Final[tuple[tuple[str, frozenset[str]], ...]] = (
    (RootCause.APR_SELECTION_INVALID, frozenset({ReasonCode.APR_NOT_FOUND})),
    (
        RootCause.TELEMETRY_UNAVAILABLE,
        frozenset({ReasonCode.TELEMETRY_NO_DATA, ReasonCode.FRESHNESS_OUTDATED}),
    ),
    (RootCause.TELEMETRY_STALE, frozenset({ReasonCode.FRESHNESS_STALE})),
    (
        RootCause.HYDRAULIC_DEPLETION_IMBALANCE,
        frozenset(
            {
                ReasonCode.DEPLETION_WEAK_RECOVERY,
                ReasonCode.TANK_DROP_CRITICAL,
                ReasonCode.TANK_DROP_WARN,
            }
        ),
    ),
    (RootCause.HYDRAULIC_RECOVERY_FAILURE, frozenset({ReasonCode.PUMP_NO_RECOVERY})),
    (
        RootCause.HYDRAULIC_DISTRIBUTION_LOSS,
        frozenset({ReasonCode.PRESSURE_LOW_NORMAL_STORAGE}),
    ),
    (RootCause.SENSOR_INSTABILITY, frozenset({ReasonCode.TANK_SENSOR_ERRATIC})),
    (
        RootCause.HYDRAULIC_OBSERVABILITY_GAP,
        frozenset({ReasonCode.HYDRAULIC_DATA_INSUFFICIENT}),
    ),
    (
        RootCause.STORAGE_DEPLETION_RISK,
        frozenset(
            {
                ReasonCode.TANK_CRITICAL,
                ReasonCode.TANK_PROJECTED_CRITICAL_2H,
                ReasonCode.TANK_LOW,
                ReasonCode.TANK_PROJECTED_LOW_2H,
            }
        ),
    ),
    (
        RootCause.PRESSURE_DEGRADATION,
        frozenset({ReasonCode.PRESSURE_CRITICAL, ReasonCode.PRESSURE_LOW}),
    ),
    (
        RootCause.WATER_QUALITY_DEGRADATION,
        frozenset({ReasonCode.TURBIDITY_CRITICAL, ReasonCode.TURBIDITY_HIGH}),
    ),
    (
        RootCause.DATA_QUALITY_DEGRADATION,
        frozenset(
            {
                ReasonCode.DATA_QUALITY_AT_RISK,
                ReasonCode.DATA_QUALITY_WATCH,
                ReasonCode.DATA_QUALITY_UNKNOWN,
            }
        ),
    ),
    (
        RootCause.KPI_RISK_SIGNAL,
        frozenset(
            {
                ReasonCode.KPI_RISK_HIGH,
                ReasonCode.KPI_RISK_MEDIUM,
                ReasonCode.PRESSURE_COMPLIANCE_LOW,
            }
        ),
    ),
)


ROOT_CAUSE_TO_RECOMMENDATION: Final[dict[str, str]] = {
    RootCause.APR_SELECTION_INVALID: "Select a valid APR ID with Silver telemetry coverage.",
    RootCause.TELEMETRY_UNAVAILABLE: "Validate telemetry connectivity and operate with field confirmation until live data recovers.",
    RootCause.TELEMETRY_STALE: "Keep operations stable and prioritize telemetry refresh in the next cycle.",
    RootCause.HYDRAULIC_DEPLETION_IMBALANCE: "Projected depletion risk detected: verify pump output, inspect losses, and initiate near-term refill control.",
    RootCause.HYDRAULIC_RECOVERY_FAILURE: "Pump is active without expected recovery: inspect pump discharge, valve positions, and potential leakage.",
    RootCause.HYDRAULIC_DISTRIBUTION_LOSS: "Low pressure with normal storage suggests distribution losses; inspect valves, PRVs, and line losses.",
    RootCause.HYDRAULIC_OBSERVABILITY_GAP: "Hydraulic trend confidence is limited; increase telemetry continuity before acting on balance assumptions.",
    RootCause.SENSOR_INSTABILITY: "Erratic tank signal detected: validate level sensor health before acting on storage trend alarms.",
    RootCause.STORAGE_DEPLETION_RISK: "Prioritize short-term refill planning and monitor storage trajectory more frequently.",
    RootCause.PRESSURE_DEGRADATION: "Investigate pressure losses and adjust pumping or valve operations to stabilize service levels.",
    RootCause.WATER_QUALITY_DEGRADATION: "Increase water quality surveillance and verify treatment performance.",
    RootCause.DATA_QUALITY_DEGRADATION: "Validate sensor data quality before relying on automated operational decisions.",
    RootCause.KPI_RISK_SIGNAL: "Review daily KPI risk drivers and schedule targeted operational checks.",
    RootCause.NORMAL_OPERATION: "Continue normal operation with routine monitoring of pressure, tank level, and turbidity.",
}


ROOT_CAUSE_CATALOG: Final[tuple[str, ...]] = tuple(ROOT_CAUSE_TO_RECOMMENDATION.keys())
OPERATIONAL_RECOMMENDATION_CATALOG: Final[tuple[str, ...]] = tuple(
    ROOT_CAUSE_TO_RECOMMENDATION[root_cause] for root_cause in ROOT_CAUSE_CATALOG
)


def derive_main_root_cause(reason_codes: Sequence[str]) -> str:
    reason_set = {str(code).strip() for code in reason_codes if str(code).strip()}
    for root_cause, trigger_codes in ROOT_CAUSE_RULES:
        if reason_set.intersection(trigger_codes):
            return root_cause
    return RootCause.NORMAL_OPERATION


def recommendation_for_root_cause(root_cause: str) -> str:
    return ROOT_CAUSE_TO_RECOMMENDATION.get(
        root_cause,
        ROOT_CAUSE_TO_RECOMMENDATION[RootCause.NORMAL_OPERATION],
    )
