// Lógica de derivación portada de src/apr_twin/dashboard/app.py:
// resumen de alertas, resumen ejecutivo, tabla de incidentes y downsampling de
// series para los gráficos. Mantiene paridad con el dashboard Streamlit.

import {
  MAX_CHART_POINTS,
  MAX_INCIDENT_ROWS,
  PRESSURE_CRITICAL_BAR,
  PRESSURE_MAX_BAR,
  PRESSURE_MIN_BAR,
  TANK_CRITICAL_PCT,
  TANK_LOW_PCT,
  TURBIDITY_ALERT_NTU,
  TURBIDITY_CRITICAL_NTU,
} from "./constants";
import type { DailyKPIRecord, TelemetryRecord, TwinState } from "./types";

export type Severity = "OK" | "WARNING" | "CRITICAL";

export interface AlertSummary {
  key: string;
  title: string;
  activeNow: boolean;
  events: number;
  maxSeverity: Severity;
  durationLabel: string;
}

export interface SummaryMetric {
  label: string;
  value: string;
  detail: string;
  tone: Severity;
}

export interface Incident {
  timestamp: string;
  event: string;
  severity: Severity;
  observedValue: string;
  threshold: string;
}

export interface ChartPoint {
  t: number; // epoch ms
  label: string; // etiqueta legible para el eje
  pressure: number | null;
  tank: number | null;
  turbidity: number | null;
}

// Cuenta los inicios de evento (flancos de subida) de una condición booleana.
function countEventStarts(flags: boolean[]): number {
  let count = 0;
  let prev = false;
  for (const cur of flags) {
    if (cur && !prev) count += 1;
    prev = cur;
  }
  return count;
}

function classifySeverity(anyWarning: boolean, anyCritical: boolean): Severity {
  if (anyCritical) return "CRITICAL";
  if (anyWarning) return "WARNING";
  return "OK";
}

function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

// Minutos de muestreo estimados (mediana de las diferencias entre timestamps).
function estimateSamplingMinutes(rows: TelemetryRecord[]): number | null {
  if (rows.length < 2) return null;
  const times = rows.map((r) => new Date(r.timestamp).getTime()).sort((a, b) => a - b);
  const diffs: number[] = [];
  for (let i = 1; i < times.length; i += 1) {
    diffs.push((times[i] - times[i - 1]) / 60000);
  }
  return median(diffs);
}

function formatMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/D";
  return `${value.toFixed(1)} min`;
}

function sumGoldDuration(gold: DailyKPIRecord[], key: keyof DailyKPIRecord): number | null {
  if (gold.length === 0) return null;
  let sum = 0;
  let seen = false;
  for (const row of gold) {
    const v = row[key];
    if (typeof v === "number" && !Number.isNaN(v)) {
      sum += v;
      seen = true;
    }
  }
  return seen ? sum : null;
}

// Construye las 4 tarjetas de resumen de alertas (presión, estanque, calidad, frescura).
export function buildAlertSummaries(
  telemetry: TelemetryRecord[],
  gold: DailyKPIRecord[],
  twin: TwinState | undefined,
): AlertSummary[] {
  const sampling = estimateSamplingMinutes(telemetry);

  const pressureFlags = telemetry.map((r) => r.pressure_bar < PRESSURE_MIN_BAR);
  const pressureCrit = telemetry.some((r) => r.pressure_bar < PRESSURE_CRITICAL_BAR);
  const tankFlags = telemetry.map((r) => r.tank_level_pct < TANK_LOW_PCT);
  const tankCrit = telemetry.some((r) => r.tank_level_pct <= TANK_CRITICAL_PCT);
  const turbFlags = telemetry.map((r) => r.turbidity_ntu > TURBIDITY_ALERT_NTU);
  const turbCrit = telemetry.some((r) => r.turbidity_ntu >= TURBIDITY_CRITICAL_NTU);

  let pressureDuration = sumGoldDuration(gold, "low_pressure_duration_minutes");
  if (pressureDuration === null && sampling !== null) {
    pressureDuration = pressureFlags.filter(Boolean).length * sampling;
  }
  let turbidityDuration = sumGoldDuration(gold, "high_turbidity_duration_minutes");
  if (turbidityDuration === null && sampling !== null) {
    turbidityDuration = turbFlags.filter(Boolean).length * sampling;
  }
  const tankDuration =
    sampling !== null ? tankFlags.filter(Boolean).length * sampling : null;

  const pressureNow = twin?.current_pressure_bar;
  const tankNow = twin?.current_tank_level_pct;
  const turbNow = twin?.current_turbidity_ntu;
  const freshness = twin?.freshness_status ?? "NO_DATA";
  const dataAge = twin?.data_age_minutes ?? null;

  // Brechas de tiempo para frescura.
  const times = telemetry
    .map((r) => new Date(r.timestamp).getTime())
    .sort((a, b) => a - b);
  const gaps: number[] = [];
  for (let i = 1; i < times.length; i += 1) gaps.push((times[i] - times[i - 1]) / 60000);
  const peakGap = gaps.length ? Math.max(...gaps) : null;
  const freshnessActive = freshness === "STALE" || freshness === "OUTDATED";

  return [
    {
      key: "pressure",
      title: "Estabilidad de presión",
      activeNow: typeof pressureNow === "number" && pressureNow < PRESSURE_MIN_BAR,
      events: countEventStarts(pressureFlags),
      maxSeverity: classifySeverity(pressureFlags.some(Boolean), pressureCrit),
      durationLabel: formatMinutes(pressureDuration),
    },
    {
      key: "tank",
      title: "Nivel de estanque",
      activeNow: typeof tankNow === "number" && tankNow < TANK_LOW_PCT,
      events: countEventStarts(tankFlags),
      maxSeverity: classifySeverity(tankFlags.some(Boolean), tankCrit),
      durationLabel: formatMinutes(tankDuration),
    },
    {
      key: "water",
      title: "Calidad del agua",
      activeNow: typeof turbNow === "number" && turbNow > TURBIDITY_ALERT_NTU,
      events: countEventStarts(turbFlags),
      maxSeverity: classifySeverity(turbFlags.some(Boolean), turbCrit),
      durationLabel: formatMinutes(turbidityDuration),
    },
    {
      key: "freshness",
      title: "Frescura de telemetría",
      activeNow: freshnessActive,
      events: gaps.filter((g) => g > 15).length,
      maxSeverity: classifySeverity(
        gaps.some((g) => g > 15),
        gaps.some((g) => g > 60),
      ),
      durationLabel: freshnessActive
        ? `Antigüedad actual ${formatMinutes(dataAge)}`
        : formatMinutes(peakGap),
    },
  ];
}

// Construye las 4 métricas del resumen ejecutivo.
export function buildExecutiveSummary(
  telemetry: TelemetryRecord[],
  gold: DailyKPIRecord[],
  twin: TwinState | undefined,
): SummaryMetric[] {
  const latestKpi = gold.length
    ? [...gold].sort((a, b) => a.date.localeCompare(b.date))[gold.length - 1]
    : null;

  // Cumplimiento de presión.
  let pressureRatio: number | null =
    typeof twin?.pressure_compliance_ratio === "number"
      ? twin.pressure_compliance_ratio
      : latestKpi?.pressure_ok_ratio ?? null;
  if (pressureRatio === null && telemetry.length) {
    const ok = telemetry.filter(
      (r) => r.pressure_bar >= PRESSURE_MIN_BAR && r.pressure_bar <= PRESSURE_MAX_BAR,
    ).length;
    pressureRatio = ok / telemetry.length;
  }
  let pressureTone: Severity = "OK";
  let pressureState = "Sin datos";
  if (pressureRatio !== null) {
    if (pressureRatio >= 0.95) {
      pressureState = "En objetivo";
      pressureTone = "OK";
    } else if (pressureRatio >= 0.9) {
      pressureState = "En observación";
      pressureTone = "WARNING";
    } else {
      pressureState = "En riesgo";
      pressureTone = "CRITICAL";
    }
  }

  // Riesgo de estanque (nivel mínimo en la ventana).
  const minTank = telemetry.length
    ? Math.min(...telemetry.map((r) => r.tank_level_pct))
    : null;
  let tankRisk = "Sin datos";
  let tankTone: Severity = "OK";
  if (minTank !== null) {
    if (minTank <= TANK_CRITICAL_PCT) {
      tankRisk = "Alto";
      tankTone = "CRITICAL";
    } else if (minTank <= TANK_LOW_PCT) {
      tankRisk = "Medio";
      tankTone = "WARNING";
    } else {
      tankRisk = "Bajo";
      tankTone = "OK";
    }
  }

  // Riesgo de calidad de agua (turbidez máxima en la ventana).
  const maxTurb = telemetry.length
    ? Math.max(...telemetry.map((r) => r.turbidity_ntu))
    : null;
  let waterRisk = "Sin datos";
  let waterTone: Severity = "OK";
  if (maxTurb !== null) {
    if (maxTurb >= TURBIDITY_CRITICAL_NTU) {
      waterRisk = "Alto";
      waterTone = "CRITICAL";
    } else if (maxTurb > TURBIDITY_ALERT_NTU) {
      waterRisk = "Medio";
      waterTone = "WARNING";
    } else {
      waterRisk = "Bajo";
      waterTone = "OK";
    }
  }

  // Completitud de datos.
  const completeness = latestKpi?.completeness_pct ?? null;
  const imputed = latestKpi?.imputed_pct ?? null;
  let completenessValue = "N/D";
  let completenessDetail = "Sin KPI en la ventana";
  let completenessTone: Severity = "OK";
  if (completeness !== null) {
    completenessValue = `${completeness.toFixed(1)}%`;
    if (completeness >= 95 && (imputed === null || imputed <= 5)) {
      completenessDetail = "Confiable";
      completenessTone = "OK";
    } else if (completeness >= 90) {
      completenessDetail = "En observación";
      completenessTone = "WARNING";
    } else {
      completenessDetail = "En riesgo";
      completenessTone = "CRITICAL";
    }
    if (imputed !== null) completenessDetail += ` · Imputado ${imputed.toFixed(1)}%`;
  }

  return [
    {
      label: "Cumplimiento de presión",
      value: pressureRatio !== null ? `${(pressureRatio * 100).toFixed(1)}%` : "N/D",
      detail: pressureState,
      tone: pressureTone,
    },
    {
      label: "Riesgo de estanque",
      value: tankRisk,
      detail: minTank !== null ? `Nivel mínimo ${minTank.toFixed(1)}%` : "Sin telemetría",
      tone: tankTone,
    },
    {
      label: "Riesgo de calidad de agua",
      value: waterRisk,
      detail:
        maxTurb !== null ? `Turbidez máxima ${maxTurb.toFixed(2)} NTU` : "Sin telemetría",
      tone: waterTone,
    },
    {
      label: "Completitud de datos",
      value: completenessValue,
      detail: completenessDetail,
      tone: completenessTone,
    },
  ];
}

// Construye la tabla de incidentes (cruces de umbral), ordenada por severidad y recencia.
export function buildIncidents(telemetry: TelemetryRecord[]): Incident[] {
  const incidents: Incident[] = [];
  for (const r of telemetry) {
    if (r.pressure_bar < PRESSURE_MIN_BAR) {
      incidents.push({
        timestamp: r.timestamp,
        event: "Presión baja",
        severity: r.pressure_bar < PRESSURE_CRITICAL_BAR ? "CRITICAL" : "WARNING",
        observedValue: `${r.pressure_bar.toFixed(2)} bar`,
        threshold: `< ${PRESSURE_MIN_BAR.toFixed(2)} bar`,
      });
    }
    if (r.tank_level_pct < TANK_LOW_PCT) {
      incidents.push({
        timestamp: r.timestamp,
        event: "Nivel de estanque bajo",
        severity: r.tank_level_pct <= TANK_CRITICAL_PCT ? "CRITICAL" : "WARNING",
        observedValue: `${r.tank_level_pct.toFixed(1)}%`,
        threshold: `< ${TANK_LOW_PCT.toFixed(1)}%`,
      });
    }
    if (r.turbidity_ntu > TURBIDITY_ALERT_NTU) {
      incidents.push({
        timestamp: r.timestamp,
        event: "Turbidez alta",
        severity: r.turbidity_ntu >= TURBIDITY_CRITICAL_NTU ? "CRITICAL" : "WARNING",
        observedValue: `${r.turbidity_ntu.toFixed(2)} NTU`,
        threshold: `> ${TURBIDITY_ALERT_NTU.toFixed(2)} NTU`,
      });
    }
  }
  const rank: Record<Severity, number> = { CRITICAL: 0, WARNING: 1, OK: 2 };
  incidents.sort((a, b) => {
    if (rank[a.severity] !== rank[b.severity]) return rank[a.severity] - rank[b.severity];
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });
  return incidents.slice(0, MAX_INCIDENT_ROWS);
}

// Reduce la serie a un máximo de puntos promediando por buckets (rendimiento de Recharts).
export function buildChartSeries(telemetry: TelemetryRecord[]): ChartPoint[] {
  const sorted = [...telemetry].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const n = sorted.length;
  if (n === 0) return [];

  const fmt = (ms: number) => {
    const d = new Date(ms);
    return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  };

  if (n <= MAX_CHART_POINTS) {
    return sorted.map((r) => {
      const t = new Date(r.timestamp).getTime();
      return {
        t,
        label: fmt(t),
        pressure: r.pressure_bar,
        tank: r.tank_level_pct,
        turbidity: r.turbidity_ntu,
      };
    });
  }

  const bucketSize = Math.ceil(n / MAX_CHART_POINTS);
  const points: ChartPoint[] = [];
  for (let i = 0; i < n; i += bucketSize) {
    const bucket = sorted.slice(i, i + bucketSize);
    const avg = (sel: (r: TelemetryRecord) => number) =>
      bucket.reduce((acc, r) => acc + sel(r), 0) / bucket.length;
    const t = new Date(bucket[Math.floor(bucket.length / 2)].timestamp).getTime();
    points.push({
      t,
      label: fmt(t),
      pressure: avg((r) => r.pressure_bar),
      tank: avg((r) => r.tank_level_pct),
      turbidity: avg((r) => r.turbidity_ntu),
    });
  }
  return points;
}
