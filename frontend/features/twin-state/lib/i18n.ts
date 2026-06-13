/**
 * Spanish (ES-CL) translation maps for API enum values and free-text strings.
 *
 * Enum dictionaries (system status, freshness, risk, etc.) are stable and keyed by the
 * exact TypeScript union values. Free-text dictionaries (alerts, root causes, recommendations)
 * are keyed by the exact English strings emitted by the backend engine and must stay in sync
 * with `src/apr_twin/twin/engine.py` and `src/apr_twin/twin/taxonomy.py`.
 *
 * Use the `t()` helper for safe lookups with a fallback to the original string.
 */

import type {
  Confidence,
  FreshnessStatus,
  HydraulicRisk,
  RiskLevel,
  SystemStatus,
  TankConsistency,
} from '@/lib/types';

/** Maps SystemStatus API values to Spanish display labels. */
export const SYSTEM_STATUS_ES: Record<SystemStatus, string> = {
  OK: 'Operativo',
  WARNING: 'Advertencia',
  CRITICAL: 'Crítico',
  NO_DATA: 'Sin datos',
};

/** Maps FreshnessStatus API values to Spanish display labels. */
export const FRESHNESS_ES: Record<FreshnessStatus, string> = {
  FRESH: 'Actualizada',
  STALE: 'Demorada',
  OUTDATED: 'Desactualizada',
  NO_DATA: 'Sin datos',
};

/** Maps RiskLevel and the synthetic "UNKNOWN" value to Spanish display labels. */
export const RISK_ES: Record<RiskLevel | 'UNKNOWN', string> = {
  LOW: 'Bajo',
  MEDIUM: 'Medio',
  HIGH: 'Alto',
  UNKNOWN: 'Desconocido',
};

/** Maps HydraulicRisk API values to Spanish display labels. */
export const HYDRAULIC_RISK_ES: Record<HydraulicRisk, string> = {
  LOW: 'Bajo',
  MEDIUM: 'Medio',
  HIGH: 'Alto',
  UNKNOWN: 'Desconocido',
};

/** Maps Confidence API values to Spanish display labels. */
export const CONFIDENCE_ES: Record<Confidence, string> = {
  LOW: 'Baja',
  MEDIUM: 'Media',
  HIGH: 'Alta',
};

/** Maps TankConsistency API values to Spanish display labels. */
export const CONSISTENCY_ES: Record<TankConsistency, string> = {
  CONSISTENT: 'Consistente',
  WATCH: 'En observación',
  INCONSISTENT: 'Inconsistente',
  UNKNOWN: 'Desconocido',
};

/**
 * Reason-code translation map keyed by ReasonCode enum values from
 * `src/apr_twin/twin/taxonomy.py`.
 */
export const REASON_CODE_ES: Record<string, string> = {
  APR_NOT_FOUND_IN_SILVER: 'APR no encontrado',
  NO_DATA_SILVER: 'Sin datos de telemetría',
  FRESHNESS_STALE: 'Telemetría demorada',
  FRESHNESS_OUTDATED: 'Telemetría desactualizada',
  PRESSURE_LOW: 'Presión baja',
  PRESSURE_CRITICAL: 'Presión crítica',
  TANK_LOW: 'Nivel de estanque bajo',
  TANK_CRITICAL: 'Nivel de estanque crítico',
  PROJECTED_TANK_LOW_2H: 'Nivel bajo proyectado a 2 h',
  PROJECTED_TANK_CRITICAL_2H: 'Nivel crítico proyectado a 2 h',
  TURBIDITY_HIGH: 'Turbidez alta',
  TURBIDITY_CRITICAL: 'Turbidez crítica',
  HYDRAULIC_PUMP_ON_NO_RECOVERY: 'Bomba sin recuperación',
  HYDRAULIC_ABNORMAL_TANK_DROP_RATE: 'Caída de estanque anómala',
  HYDRAULIC_ABNORMAL_TANK_DROP_RATE_CRITICAL: 'Caída de estanque crítica',
  HYDRAULIC_LOW_PRESSURE_WITH_NORMAL_STORAGE: 'Presión baja con almacenamiento normal',
  HYDRAULIC_PROJECTED_DEPLETION_INSUFFICIENT_RECOVERY: 'Vaciamiento con recuperación débil',
  HYDRAULIC_TANK_SENSOR_ERRATIC: 'Sensor de nivel errático',
  HYDRAULIC_BALANCE_WATCH: 'Balance hidráulico en observación',
  HYDRAULIC_BALANCE_INCONSISTENT: 'Balance hidráulico inconsistente',
  HYDRAULIC_RISK_MEDIUM: 'Riesgo hidráulico medio',
  HYDRAULIC_RISK_HIGH: 'Riesgo hidráulico alto',
  PRESSURE_COMPLIANCE_BELOW_TARGET: 'Cumplimiento de presión bajo',
  DAILY_RISK_MEDIUM: 'Riesgo diario medio',
  DAILY_RISK_HIGH: 'Riesgo diario alto',
  DATA_COMPLETENESS_WATCH: 'Completitud de datos en observación',
  DATA_COMPLETENESS_AT_RISK: 'Completitud de datos en riesgo',
  DATA_COMPLETENESS_UNKNOWN: 'Completitud de datos desconocida',
};

/**
 * Active-alert translation map keyed by the exact free-text strings emitted by
 * `src/apr_twin/twin/engine.py` in the `active_alerts` field.
 */
export const ALERT_ES: Record<string, string> = {
  'No Silver telemetry data available.': 'No hay datos de telemetría disponibles.',
  'Low pressure': 'Presión baja',
  'Low tank level': 'Nivel de estanque bajo',
  'Projected low tank level in 2 hours': 'Nivel de estanque bajo proyectado en 2 horas',
  'Projected critical tank level in 2 hours': 'Nivel de estanque crítico proyectado en 2 horas',
  'Pump on but tank level not recovering': 'Bomba encendida pero el estanque no se recupera',
  'Abnormal tank drop rate': 'Tasa de caída de estanque anómala',
  'Low pressure with normal storage': 'Presión baja con almacenamiento normal',
  'Projected depletion risk with insufficient recovery':
    'Riesgo de vaciamiento proyectado con recuperación insuficiente',
  'Noisy or erratic tank level signal': 'Señal de nivel de estanque ruidosa o errática',
  'High turbidity': 'Turbidez alta',
  'Pressure compliance below target': 'Cumplimiento de presión bajo el objetivo',
  'Telemetry data is stale': 'La telemetría está demorada',
  'Telemetry data is outdated': 'La telemetría está desactualizada',
};

/**
 * Root-cause translation map keyed by the exact free-text strings emitted by
 * `src/apr_twin/twin/engine.py` in the `possible_root_cause` field.
 */
export const ROOT_CAUSE_ES: Record<string, string> = {
  'Net outflow is exceeding recovery capacity.':
    'El caudal de salida supera la capacidad de recuperación.',
  'Pump is running but storage is not recovering as expected.':
    'La bomba está operando pero el almacenamiento no se recupera como se espera.',
  'Distribution-side hydraulic losses are likely despite normal storage.':
    'Probables pérdidas hidráulicas en la distribución pese a un almacenamiento normal.',
  'Tank level sensor appears noisy or erratic.':
    'El sensor de nivel del estanque parece ruidoso o errático.',
  'Tank level is dropping faster than typical demand behavior.':
    'El nivel del estanque cae más rápido que el comportamiento típico de demanda.',
  'Not enough recent telemetry to infer hydraulic behavior.':
    'No hay suficiente telemetría reciente para inferir el comportamiento hidráulico.',
  'Recent tank trend is consistent with recovery.':
    'La tendencia reciente del estanque es consistente con una recuperación.',
  'Recent tank decline appears demand-driven under current operation.':
    'La caída reciente del estanque parece impulsada por la demanda bajo la operación actual.',
  'No telemetry available to infer hydraulic behavior.':
    'No hay telemetría disponible para inferir el comportamiento hidráulico.',
};

/**
 * Operational-recommendation translation map keyed by the fixed catalog of recommendation
 * strings defined in `src/apr_twin/twin/taxonomy.py` and emitted by `engine.py`.
 */
export const RECOMMENDATION_ES: Record<string, string> = {
  'Select a valid APR ID with Silver telemetry coverage.':
    'Seleccione un APR válido con cobertura de telemetría.',
  'Validate telemetry connectivity and operate with field confirmation until live data recovers.':
    'Valide la conectividad de telemetría y opere con confirmación en terreno hasta que se recuperen los datos en vivo.',
  'Keep operations stable and prioritize telemetry refresh in the next cycle.':
    'Mantenga la operación estable y priorice la actualización de telemetría en el próximo ciclo.',
  'Projected depletion risk detected: verify pump output, inspect losses, and initiate near-term refill control.':
    'Riesgo de vaciamiento proyectado: verifique el caudal de la bomba, inspeccione pérdidas e inicie control de rellenado a corto plazo.',
  'Pump is active without expected recovery: inspect pump discharge, valve positions, and potential leakage.':
    'Bomba activa sin la recuperación esperada: inspeccione la descarga de la bomba, posición de válvulas y posibles fugas.',
  'Low pressure with normal storage suggests distribution losses; inspect valves, PRVs, and line losses.':
    'Presión baja con almacenamiento normal sugiere pérdidas en distribución; inspeccione válvulas, reductoras de presión y pérdidas en líneas.',
  'Hydraulic trend confidence is limited; increase telemetry continuity before acting on balance assumptions.':
    'La confianza en la tendencia hidráulica es limitada; aumente la continuidad de telemetría antes de actuar sobre supuestos de balance.',
  'Erratic tank signal detected: validate level sensor health before acting on storage trend alarms.':
    'Señal de estanque errática: valide el estado del sensor de nivel antes de actuar sobre alarmas de tendencia de almacenamiento.',
  'Prioritize short-term refill planning and monitor storage trajectory more frequently.':
    'Priorice la planificación de rellenado a corto plazo y monitoree la trayectoria de almacenamiento con mayor frecuencia.',
  'Investigate pressure losses and adjust pumping or valve operations to stabilize service levels.':
    'Investigue pérdidas de presión y ajuste el bombeo o la operación de válvulas para estabilizar los niveles de servicio.',
  'Increase water quality surveillance and verify treatment performance.':
    'Aumente la vigilancia de calidad del agua y verifique el desempeño del tratamiento.',
  'Validate sensor data quality before relying on automated operational decisions.':
    'Valide la calidad de los datos de sensores antes de confiar en decisiones operacionales automatizadas.',
  'Review daily KPI risk drivers and schedule targeted operational checks.':
    'Revise los factores de riesgo de los KPI diarios y programe inspecciones operacionales dirigidas.',
  'Continue normal operation with routine monitoring of pressure, tank level, and turbidity.':
    'Continúe la operación normal con monitoreo de rutina de presión, nivel de estanque y turbidez.',
  'Review data quality trends and confirm telemetry consistency during shifts.':
    'Revise las tendencias de calidad de datos y confirme la consistencia de la telemetría durante los turnos.',
};

/**
 * Translates a free-text string by looking it up in the provided dictionary.
 * Falls back to the trimmed original value when no translation is found.
 *
 * Handles two parameterized patterns inline:
 * - `"Daily risk level: HIGH"` → `"Nivel de riesgo diario: Alto"`
 * - `"Hydraulic inconsistency detected. Likely cause: <cause>"` → translated compound string
 *
 * @param dict - Translation dictionary to search.
 * @param value - The source string to translate. Null/undefined returns an empty string.
 * @returns The Spanish translation, or the trimmed original if no match exists.
 */
export function t(dict: Record<string, string>, value: string | null | undefined): string {
  if (!value) return '';
  const trimmed = value.trim();
  if (dict[trimmed]) return dict[trimmed];
  const riskMatch = /^Daily risk level:\s*(LOW|MEDIUM|HIGH)$/.exec(trimmed);
  if (riskMatch) {
    return `Nivel de riesgo diario: ${RISK_ES[riskMatch[1] as RiskLevel]}`;
  }
  const hydMatch = /^Hydraulic inconsistency detected\. Likely cause:\s*(.+)$/.exec(trimmed);
  if (hydMatch) {
    const cause = ROOT_CAUSE_ES[hydMatch[1].trim()] ?? hydMatch[1].trim();
    return `Inconsistencia hidráulica detectada. Causa probable: ${cause}`;
  }
  return trimmed;
}
