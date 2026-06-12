// Traducciones al español de los valores que la API entrega en inglés.
// Los enums (estado, frescura, riesgo, etc.) son estables; los textos libres
// (alertas, causa raíz, recomendación) se mapean por su string exacto, con
// fallback al texto original si no hay coincidencia (ver `t()`).

import type {
  Confidence,
  FreshnessStatus,
  HydraulicRisk,
  RiskLevel,
  SystemStatus,
  TankConsistency,
} from "@/lib/types";

export const SYSTEM_STATUS_ES: Record<SystemStatus, string> = {
  OK: "Operativo",
  WARNING: "Advertencia",
  CRITICAL: "Crítico",
  NO_DATA: "Sin datos",
};

export const FRESHNESS_ES: Record<FreshnessStatus, string> = {
  FRESH: "Actualizada",
  STALE: "Demorada",
  OUTDATED: "Desactualizada",
  NO_DATA: "Sin datos",
};

export const RISK_ES: Record<RiskLevel | "UNKNOWN", string> = {
  LOW: "Bajo",
  MEDIUM: "Medio",
  HIGH: "Alto",
  UNKNOWN: "Desconocido",
};

export const HYDRAULIC_RISK_ES: Record<HydraulicRisk, string> = {
  LOW: "Bajo",
  MEDIUM: "Medio",
  HIGH: "Alto",
  UNKNOWN: "Desconocido",
};

export const CONFIDENCE_ES: Record<Confidence, string> = {
  LOW: "Baja",
  MEDIUM: "Media",
  HIGH: "Alta",
};

export const CONSISTENCY_ES: Record<TankConsistency, string> = {
  CONSISTENT: "Consistente",
  WATCH: "En observación",
  INCONSISTENT: "Inconsistente",
  UNKNOWN: "Desconocido",
};

// Códigos de razón del gemelo (src/apr_twin/twin/taxonomy.py::ReasonCode).
export const REASON_CODE_ES: Record<string, string> = {
  APR_NOT_FOUND: "APR no encontrado",
  TELEMETRY_NO_DATA: "Sin datos de telemetría",
  FRESHNESS_STALE: "Telemetría demorada",
  FRESHNESS_OUTDATED: "Telemetría desactualizada",
  PRESSURE_LOW: "Presión baja",
  PRESSURE_CRITICAL: "Presión crítica",
  TANK_LOW: "Nivel de estanque bajo",
  TANK_CRITICAL: "Nivel de estanque crítico",
  TANK_PROJECTED_LOW_2H: "Nivel bajo proyectado a 2 h",
  TANK_PROJECTED_CRITICAL_2H: "Nivel crítico proyectado a 2 h",
  TURBIDITY_HIGH: "Turbidez alta",
  TURBIDITY_CRITICAL: "Turbidez crítica",
  PUMP_NO_RECOVERY: "Bomba sin recuperación",
  TANK_DROP_WARN: "Caída de estanque anómala",
  TANK_DROP_CRITICAL: "Caída de estanque crítica",
  PRESSURE_LOW_NORMAL_STORAGE: "Presión baja con almacenamiento normal",
  DEPLETION_WEAK_RECOVERY: "Vaciamiento con recuperación débil",
  TANK_SENSOR_ERRATIC: "Sensor de nivel errático",
  HYDRAULIC_DATA_INSUFFICIENT: "Datos hidráulicos insuficientes",
  PRESSURE_COMPLIANCE_LOW: "Cumplimiento de presión bajo",
  KPI_RISK_MEDIUM: "Riesgo KPI medio",
  KPI_RISK_HIGH: "Riesgo KPI alto",
  DATA_QUALITY_WATCH: "Calidad de datos en observación",
  DATA_QUALITY_AT_RISK: "Calidad de datos en riesgo",
  DATA_QUALITY_UNKNOWN: "Calidad de datos desconocida",
};

// Alertas activas (textos libres en engine.py::active_alerts).
export const ALERT_ES: Record<string, string> = {
  "No Silver telemetry data available.": "No hay datos de telemetría disponibles.",
  "Low pressure": "Presión baja",
  "Low tank level": "Nivel de estanque bajo",
  "Projected low tank level in 2 hours": "Nivel de estanque bajo proyectado en 2 horas",
  "Projected critical tank level in 2 hours": "Nivel de estanque crítico proyectado en 2 horas",
  "Pump on but tank level not recovering": "Bomba encendida pero el estanque no se recupera",
  "Abnormal tank drop rate": "Tasa de caída de estanque anómala",
  "Low pressure with normal storage": "Presión baja con almacenamiento normal",
  "Projected depletion risk with insufficient recovery":
    "Riesgo de vaciamiento proyectado con recuperación insuficiente",
  "Noisy or erratic tank level signal": "Señal de nivel de estanque ruidosa o errática",
  "High turbidity": "Turbidez alta",
  "Pressure compliance below target": "Cumplimiento de presión bajo el objetivo",
  "Telemetry data is stale": "La telemetría está demorada",
  "Telemetry data is outdated": "La telemetría está desactualizada",
};

// Causas raíz probables (textos libres en engine.py::possible_root_cause).
export const ROOT_CAUSE_ES: Record<string, string> = {
  "Net outflow is exceeding recovery capacity.":
    "El caudal de salida supera la capacidad de recuperación.",
  "Pump is running but storage is not recovering as expected.":
    "La bomba está operando pero el almacenamiento no se recupera como se espera.",
  "Distribution-side hydraulic losses are likely despite normal storage.":
    "Probables pérdidas hidráulicas en la distribución pese a un almacenamiento normal.",
  "Tank level sensor appears noisy or erratic.":
    "El sensor de nivel del estanque parece ruidoso o errático.",
  "Tank level is dropping faster than typical demand behavior.":
    "El nivel del estanque cae más rápido que el comportamiento típico de demanda.",
  "Not enough recent telemetry to infer hydraulic behavior.":
    "No hay suficiente telemetría reciente para inferir el comportamiento hidráulico.",
  "Recent tank trend is consistent with recovery.":
    "La tendencia reciente del estanque es consistente con una recuperación.",
  "Recent tank decline appears demand-driven under current operation.":
    "La caída reciente del estanque parece impulsada por la demanda bajo la operación actual.",
  "No telemetry available to infer hydraulic behavior.":
    "No hay telemetría disponible para inferir el comportamiento hidráulico.",
};

// Recomendaciones operacionales (catálogo fijo en taxonomy.py + engine.py).
export const RECOMMENDATION_ES: Record<string, string> = {
  "Select a valid APR ID with Silver telemetry coverage.":
    "Seleccione un APR válido con cobertura de telemetría.",
  "Validate telemetry connectivity and operate with field confirmation until live data recovers.":
    "Valide la conectividad de telemetría y opere con confirmación en terreno hasta que se recuperen los datos en vivo.",
  "Keep operations stable and prioritize telemetry refresh in the next cycle.":
    "Mantenga la operación estable y priorice la actualización de telemetría en el próximo ciclo.",
  "Projected depletion risk detected: verify pump output, inspect losses, and initiate near-term refill control.":
    "Riesgo de vaciamiento proyectado: verifique el caudal de la bomba, inspeccione pérdidas e inicie control de rellenado a corto plazo.",
  "Pump is active without expected recovery: inspect pump discharge, valve positions, and potential leakage.":
    "Bomba activa sin la recuperación esperada: inspeccione la descarga de la bomba, posición de válvulas y posibles fugas.",
  "Low pressure with normal storage suggests distribution losses; inspect valves, PRVs, and line losses.":
    "Presión baja con almacenamiento normal sugiere pérdidas en distribución; inspeccione válvulas, reductoras de presión y pérdidas en líneas.",
  "Hydraulic trend confidence is limited; increase telemetry continuity before acting on balance assumptions.":
    "La confianza en la tendencia hidráulica es limitada; aumente la continuidad de telemetría antes de actuar sobre supuestos de balance.",
  "Erratic tank signal detected: validate level sensor health before acting on storage trend alarms.":
    "Señal de estanque errática: valide el estado del sensor de nivel antes de actuar sobre alarmas de tendencia de almacenamiento.",
  "Prioritize short-term refill planning and monitor storage trajectory more frequently.":
    "Priorice la planificación de rellenado a corto plazo y monitoree la trayectoria de almacenamiento con mayor frecuencia.",
  "Investigate pressure losses and adjust pumping or valve operations to stabilize service levels.":
    "Investigue pérdidas de presión y ajuste el bombeo o la operación de válvulas para estabilizar los niveles de servicio.",
  "Increase water quality surveillance and verify treatment performance.":
    "Aumente la vigilancia de calidad del agua y verifique el desempeño del tratamiento.",
  "Validate sensor data quality before relying on automated operational decisions.":
    "Valide la calidad de los datos de sensores antes de confiar en decisiones operacionales automatizadas.",
  "Review daily KPI risk drivers and schedule targeted operational checks.":
    "Revise los factores de riesgo de los KPI diarios y programe inspecciones operacionales dirigidas.",
  "Continue normal operation with routine monitoring of pressure, tank level, and turbidity.":
    "Continúe la operación normal con monitoreo de rutina de presión, nivel de estanque y turbidez.",
  "Review data quality trends and confirm telemetry consistency during shifts.":
    "Revise las tendencias de calidad de datos y confirme la consistencia de la telemetría durante los turnos.",
};

// Traduce un texto libre buscándolo en el diccionario indicado; si no existe,
// devuelve el texto original (fallback seguro).
export function t(dict: Record<string, string>, value: string | null | undefined): string {
  if (!value) return "";
  const trimmed = value.trim();
  if (dict[trimmed]) return dict[trimmed];
  // Caso especial: "Daily risk level: HIGH" -> "Nivel de riesgo diario: Alto"
  const riskMatch = /^Daily risk level:\s*(LOW|MEDIUM|HIGH)$/.exec(trimmed);
  if (riskMatch) {
    return `Nivel de riesgo diario: ${RISK_ES[riskMatch[1] as RiskLevel]}`;
  }
  // Caso especial: recomendación de inconsistencia hidráulica con causa interpolada.
  const hydMatch = /^Hydraulic inconsistency detected\. Likely cause:\s*(.+)$/.exec(trimmed);
  if (hydMatch) {
    const cause = ROOT_CAUSE_ES[hydMatch[1].trim()] ?? hydMatch[1].trim();
    return `Inconsistencia hidráulica detectada. Causa probable: ${cause}`;
  }
  return trimmed;
}
