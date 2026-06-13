import {
  MAX_CHART_POINTS,
  MAX_INCIDENT_ROWS,
  PRESSURE_CRITICAL_BAR,
  PRESSURE_MIN_BAR,
  TANK_CRITICAL_PCT,
  TANK_LOW_PCT,
  TURBIDITY_ALERT_NTU,
  TURBIDITY_CRITICAL_NTU,
} from '@/lib/constants';
import type { TelemetryRecord } from '@/lib/types';
import type { ChartPoint, Incident, Severity } from '../types';

/** Formats a millisecond epoch timestamp as "DD/MM HH:MM" for chart axis labels. */
const fmt = (ms: number) => {
  const d = new Date(ms);
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')} ${String(d.getHours())
    .padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

/**
 * Converts a raw telemetry array into downsampled chart points suitable for Recharts rendering.
 *
 * When the record count exceeds MAX_CHART_POINTS, records are grouped into equal-sized buckets
 * and each bucket is collapsed to the average of its values (pressure, tank, turbidity), using
 * the median record's timestamp as the representative point.
 *
 * @param telemetry - Unsorted raw telemetry records from the API.
 * @returns Array of ChartPoint objects sorted chronologically.
 */
export function buildChartSeries(telemetry: TelemetryRecord[]): ChartPoint[] {
  const sorted = [...telemetry].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const n = sorted.length;
  if (n === 0) return [];

  if (n <= MAX_CHART_POINTS) {
    return sorted.map((r) => {
      const t = new Date(r.timestamp).getTime();
      return { t, label: fmt(t), pressure: r.pressure_bar, tank: r.tank_level_pct, turbidity: r.turbidity_ntu };
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

/**
 * Derives threshold-crossing incidents from a raw telemetry array.
 *
 * Evaluates three dimensions per record:
 * - Pressure below PRESSURE_MIN_BAR (CRITICAL if below PRESSURE_CRITICAL_BAR)
 * - Tank level below TANK_LOW_PCT (CRITICAL if at or below TANK_CRITICAL_PCT)
 * - Turbidity above TURBIDITY_ALERT_NTU (CRITICAL if at or above TURBIDITY_CRITICAL_NTU)
 *
 * Results are sorted CRITICAL-first, then by descending timestamp within each severity tier.
 * The output is capped at MAX_INCIDENT_ROWS.
 *
 * @param telemetry - Raw telemetry records in any order.
 * @returns Sorted and capped array of Incident objects.
 */
export function buildIncidents(telemetry: TelemetryRecord[]): Incident[] {
  const incidents: Incident[] = [];
  for (const r of telemetry) {
    if (r.pressure_bar < PRESSURE_MIN_BAR) {
      incidents.push({
        timestamp: r.timestamp,
        event: 'Presión baja',
        severity: r.pressure_bar < PRESSURE_CRITICAL_BAR ? 'CRITICAL' : 'WARNING',
        observedValue: `${r.pressure_bar.toFixed(2)} bar`,
        threshold: `< ${PRESSURE_MIN_BAR.toFixed(2)} bar`,
      });
    }
    if (r.tank_level_pct < TANK_LOW_PCT) {
      incidents.push({
        timestamp: r.timestamp,
        event: 'Nivel de estanque bajo',
        severity: r.tank_level_pct <= TANK_CRITICAL_PCT ? 'CRITICAL' : 'WARNING',
        observedValue: `${r.tank_level_pct.toFixed(1)}%`,
        threshold: `< ${TANK_LOW_PCT.toFixed(1)}%`,
      });
    }
    if (r.turbidity_ntu > TURBIDITY_ALERT_NTU) {
      incidents.push({
        timestamp: r.timestamp,
        event: 'Turbidez alta',
        severity: r.turbidity_ntu >= TURBIDITY_CRITICAL_NTU ? 'CRITICAL' : 'WARNING',
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
