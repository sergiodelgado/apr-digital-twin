import type { AvailableAPRRecord } from '@/lib/types';

/** Date range and APR selection filters used by the control-room data hooks. */
export interface Filters {
  aprId: string | null;
  /** yyyy-mm-dd inclusive start date. */
  startDate: string;
  /** yyyy-mm-dd inclusive end date. */
  endDate: string;
}

/**
 * Derives the available date bounds (min/max as yyyy-mm-dd strings) from an APR
 * record's telemetry and KPI timestamps.
 *
 * Considers all four timestamp fields: first/last telemetry and first/last KPI date.
 * Returns null if the record is undefined or has no date information at all.
 *
 * @param apr - The APR catalog record to inspect. May be undefined while the catalog loads.
 * @returns An object with `min` and `max` date strings, or null.
 */
export function dateBoundsFor(
  apr: AvailableAPRRecord | undefined,
): { min: string; max: string } | null {
  if (!apr) return null;
  const candidates = [
    apr.first_telemetry_timestamp,
    apr.last_telemetry_timestamp,
    apr.first_kpi_date,
    apr.last_kpi_date,
  ]
    .filter((v): v is string => Boolean(v))
    .map((v) => v.slice(0, 10));
  if (candidates.length === 0) return null;
  return {
    min: candidates.reduce((a, b) => (a < b ? a : b)),
    max: candidates.reduce((a, b) => (a > b ? a : b)),
  };
}
