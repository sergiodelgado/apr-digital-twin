import type { AvailableAPRRecord } from "@/lib/types";

export interface Filters {
  aprId: string | null;
  startDate: string; // yyyy-mm-dd
  endDate: string;   // yyyy-mm-dd
}

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
