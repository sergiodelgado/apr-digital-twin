import {
  FRESHNESS_FRESH_MAX_MINUTES,
  PRESSURE_CRITICAL_BAR,
  PRESSURE_MAX_BAR,
  PRESSURE_MIN_BAR,
  TANK_CRITICAL_PCT,
  TANK_LOW_PCT,
  TURBIDITY_ALERT_NTU,
  TURBIDITY_CRITICAL_NTU,
} from '@/lib/constants';
import type { DailyKPIRecord, Severity, TelemetryRecord, TwinState } from '@/lib/types';
import type { AlertSummary, SummaryMetric } from '../types';

/**
 * Counts the number of distinct rising-edge transitions in a boolean flag array.
 * A transition is counted when a value changes from false to true.
 *
 * @param flags - Ordered boolean array (e.g. per-record threshold-crossing flags).
 * @returns Number of distinct event starts.
 */
function countEventStarts(flags: boolean[]): number {
  let count = 0;
  let prev = false;
  for (const cur of flags) {
    if (cur && !prev) count += 1;
    prev = cur;
  }
  return count;
}

/**
 * Classifies the worst-case severity given two boolean inputs.
 *
 * @param anyWarning - True if at least one WARNING-level breach was observed.
 * @param anyCritical - True if at least one CRITICAL-level breach was observed.
 * @returns The highest applicable Severity: CRITICAL > WARNING > OK.
 */
function classifySeverity(anyWarning: boolean, anyCritical: boolean): Severity {
  if (anyCritical) return 'CRITICAL';
  if (anyWarning) return 'WARNING';
  return 'OK';
}

/**
 * Computes the median of a numeric array.
 *
 * @param values - Array of numbers.
 * @returns The median value, or null for an empty array.
 */
function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (
    sorted[mid - 1] + sorted[mid]
  ) / 2;
}

/**
 * Estimates the median sampling interval of a telemetry series in minutes.
 * Used as a multiplier to convert flag counts into approximate event durations
 * when Gold KPI duration fields are unavailable.
 *
 * @param rows - Raw telemetry records (any order).
 * @returns Median gap in minutes between consecutive readings, or null if fewer than 2 records.
 */
function estimateSamplingMinutes(rows: TelemetryRecord[]): number | null {
  if (rows.length < 2) return null;
  const times = rows.map((r) => new Date(r.timestamp).getTime()).sort((a, b) => a - b);
  const diffs: number[] = [];
  for (let i = 1; i < times.length; i += 1) diffs.push((
    times[i] - times[i - 1]
  ) / 60000);
  return median(diffs);
}

/**
 * Formats a duration in minutes as a localized string (e.g. "12.5 min").
 * Returns "N/D" for null, undefined, or NaN values.
 *
 * @param value - Duration in minutes.
 * @returns Formatted string.
 */
function formatMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/D';
  return `${value.toFixed(1)} min`;
}

/**
 * Sums a numeric Gold KPI column across all records in the window.
 * Returns null if the Gold array is empty or the column contains no valid numbers.
 *
 * @param gold - Daily KPI records for the selected date range.
 * @param key - Column name to sum.
 * @returns Sum of all valid (non-NaN) values, or null.
 */
function sumGoldDuration(gold: DailyKPIRecord[], key: keyof DailyKPIRecord): number | null {
  if (gold.length === 0) return null;
  let sum = 0;
  let seen = false;
  for (const row of gold) {
    const v = row[key];
    if (typeof v === 'number' && !Number.isNaN(v)) {
      sum += v;
      seen = true;
    }
  }
  return seen ? sum : null;
}

/**
 * Builds the four AlertSummary objects (pressure, tank, water quality, freshness)
 * for the selected time window.
 *
 * Duration estimates prefer Gold KPI duration fields when available; when absent,
 * they fall back to `flag count × estimated sampling interval`.
 *
 * @param telemetry - Raw telemetry records for the window.
 * @param gold - Daily KPI records for the window.
 * @param twin - Current twin state; used for "active now" checks and freshness age.
 * @returns Array of four AlertSummary objects in display order.
 */
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

  let pressureDuration = sumGoldDuration(gold, 'low_pressure_duration_minutes');
  if (pressureDuration === null && sampling !== null)
    pressureDuration = pressureFlags.filter(Boolean).length * sampling;

  let turbidityDuration = sumGoldDuration(gold, 'high_turbidity_duration_minutes');
  if (turbidityDuration === null && sampling !== null)
    turbidityDuration = turbFlags.filter(Boolean).length * sampling;

  const tankDuration = sampling !== null ? tankFlags.filter(Boolean).length * sampling : null;

  const pressureNow = twin?.current_pressure_bar;
  const tankNow = twin?.current_tank_level_pct;
  const turbNow = twin?.current_turbidity_ntu;
  const freshness = twin?.freshness_status ?? 'NO_DATA';
  const dataAge = twin?.data_age_minutes ?? null;

  const times = telemetry.map((r) => new Date(r.timestamp).getTime()).sort((a, b) => a - b);
  const gaps: number[] = [];
  for (let i = 1; i < times.length; i += 1) gaps.push((
    times[i] - times[i - 1]
  ) / 60000);
  const peakGap = gaps.length ? Math.max(...gaps) : null;
  const freshnessActive = freshness === 'STALE' || freshness === 'OUTDATED';

  return [
    {
      key: 'pressure',
      title: 'Estabilidad de presión',
      activeNow: typeof pressureNow === 'number' && pressureNow < PRESSURE_MIN_BAR,
      events: countEventStarts(pressureFlags),
      maxSeverity: classifySeverity(pressureFlags.some(Boolean), pressureCrit),
      durationLabel: formatMinutes(pressureDuration),
    },
    {
      key: 'tank',
      title: 'Nivel de estanque',
      activeNow: typeof tankNow === 'number' && tankNow < TANK_LOW_PCT,
      events: countEventStarts(tankFlags),
      maxSeverity: classifySeverity(tankFlags.some(Boolean), tankCrit),
      durationLabel: formatMinutes(tankDuration),
    },
    {
      key: 'water',
      title: 'Calidad del agua',
      activeNow: typeof turbNow === 'number' && turbNow > TURBIDITY_ALERT_NTU,
      events: countEventStarts(turbFlags),
      maxSeverity: classifySeverity(turbFlags.some(Boolean), turbCrit),
      durationLabel: formatMinutes(turbidityDuration),
    },
    {
      key: 'freshness',
      title: 'Frescura de telemetría',
      activeNow: freshnessActive,
      events: gaps.filter((g) => g > FRESHNESS_FRESH_MAX_MINUTES).length,
      maxSeverity: classifySeverity(
        gaps.some((g) => g > FRESHNESS_FRESH_MAX_MINUTES),
        gaps.some((g) => g > 60),
      ),
      durationLabel: freshnessActive
        ? `Antigüedad actual ${formatMinutes(dataAge)}`
        : formatMinutes(peakGap),
    },
  ];
}

/**
 * Builds the four executive-summary SummaryMetric objects for the selected window:
 * pressure compliance, tank risk, water-quality risk, and data completeness.
 *
 * Pressure compliance is sourced from: twin state → latest Gold KPI → raw telemetry ratio,
 * in that priority order.
 *
 * @param telemetry - Raw telemetry records for the window.
 * @param gold - Daily KPI records for the window.
 * @param twin - Current twin state; used for pressure compliance and projected values.
 * @returns Array of four SummaryMetric objects in display order.
 */
export function buildExecutiveSummary(
  telemetry: TelemetryRecord[],
  gold: DailyKPIRecord[],
  twin: TwinState | undefined,
): SummaryMetric[] {
  const latestKpi = gold.length
    ? [...gold].sort((a, b) => a.date.localeCompare(b.date))[gold.length - 1]
    : null;

  let pressureRatio: number | null =
    typeof twin?.pressure_compliance_ratio === 'number'
      ? twin.pressure_compliance_ratio
      : (
        latestKpi?.pressure_ok_ratio ?? null
      );
  if (pressureRatio === null && telemetry.length) {
    const ok = telemetry.filter(
      (r) => r.pressure_bar >= PRESSURE_MIN_BAR && r.pressure_bar <= PRESSURE_MAX_BAR,
    ).length;
    pressureRatio = ok / telemetry.length;
  }
  let pressureTone: Severity = 'OK';
  let pressureState = 'Sin datos';
  if (pressureRatio !== null) {
    if (pressureRatio >= 0.95) {
      pressureState = 'En objetivo';
      pressureTone = 'OK';
    } else if (pressureRatio >= 0.9) {
      pressureState = 'En observación';
      pressureTone = 'WARNING';
    } else {
      pressureState = 'En riesgo';
      pressureTone = 'CRITICAL';
    }
  }

  const minTank = telemetry.length ? Math.min(...telemetry.map((r) => r.tank_level_pct)) : null;
  let tankRisk = 'Sin datos';
  let tankTone: Severity = 'OK';
  if (minTank !== null) {
    if (minTank <= TANK_CRITICAL_PCT) {
      tankRisk = 'Alto';
      tankTone = 'CRITICAL';
    } else if (minTank <= TANK_LOW_PCT) {
      tankRisk = 'Medio';
      tankTone = 'WARNING';
    } else {
      tankRisk = 'Bajo';
      tankTone = 'OK';
    }
  }

  const maxTurb = telemetry.length ? Math.max(...telemetry.map((r) => r.turbidity_ntu)) : null;
  let waterRisk = 'Sin datos';
  let waterTone: Severity = 'OK';
  if (maxTurb !== null) {
    if (maxTurb >= TURBIDITY_CRITICAL_NTU) {
      waterRisk = 'Alto';
      waterTone = 'CRITICAL';
    } else if (maxTurb > TURBIDITY_ALERT_NTU) {
      waterRisk = 'Medio';
      waterTone = 'WARNING';
    } else {
      waterRisk = 'Bajo';
      waterTone = 'OK';
    }
  }

  const completeness = latestKpi?.completeness_pct ?? null;
  const imputed = latestKpi?.imputed_pct ?? null;
  let completenessValue = 'N/D';
  let completenessDetail = 'Sin KPI en la ventana';
  let completenessTone: Severity = 'OK';
  if (completeness !== null) {
    completenessValue = `${completeness.toFixed(1)}%`;
    if (completeness >= 95 && (
      imputed === null || imputed <= 5
    )) {
      completenessDetail = 'Confiable';
      completenessTone = 'OK';
    } else if (completeness >= 90) {
      completenessDetail = 'En observación';
      completenessTone = 'WARNING';
    } else {
      completenessDetail = 'En riesgo';
      completenessTone = 'CRITICAL';
    }
    if (imputed !== null) completenessDetail += ` · Imputado ${imputed.toFixed(1)}%`;
  }

  return [
    {
      label: 'Cumplimiento de presión',
      value: pressureRatio !== null ? `${(
        pressureRatio * 100
      ).toFixed(1)}%` : 'N/D',
      detail: pressureState,
      tone: pressureTone,
    },
    {
      label: 'Riesgo de estanque',
      value: tankRisk,
      detail: minTank !== null ? `Nivel mínimo ${minTank.toFixed(1)}%` : 'Sin telemetría',
      tone: tankTone,
    },
    {
      label: 'Riesgo de calidad de agua',
      value: waterRisk,
      detail: maxTurb !== null ? `Turbidez máxima ${maxTurb.toFixed(2)} NTU` : 'Sin telemetría',
      tone: waterTone,
    },
    {
      label: 'Completitud de datos',
      value: completenessValue,
      detail: completenessDetail,
      tone: completenessTone,
    },
  ];
}
