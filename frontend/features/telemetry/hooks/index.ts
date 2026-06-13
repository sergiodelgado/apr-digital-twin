import useSWR from 'swr';
import { fetcher, qs, SWR_CONFIG } from '@/lib/api/fetcher';
import { API_BASE } from '@/lib/constants';
import type { DailyKPIRecord, TelemetryRecord } from '@/lib/types';

/**
 * SWR hook that fetches raw telemetry records for a given APR and ISO 8601 datetime window.
 * Suspends the request (null key) when any required parameter is missing.
 *
 * @param aprId - APR identifier. Pass null to suspend the fetch.
 * @param start - ISO 8601 datetime string for the start of the window (inclusive).
 * @param end - ISO 8601 datetime string for the end of the window (inclusive).
 * @returns SWR response with a `TelemetryRecord[]` array.
 */
export function useTelemetry(
  aprId: string | null,
  start: string | null,
  end: string | null,
) {
  const key =
    aprId && start && end
      ? `${API_BASE}/telemetry/recent${qs({ apr_id: aprId, start, end, limit: 5000 })}`
      : null;
  return useSWR<TelemetryRecord[]>(key, fetcher, SWR_CONFIG);
}

/**
 * SWR hook that fetches daily KPI aggregation records for a given APR and date range.
 * Suspends the request (null key) when any required parameter is missing.
 *
 * @param aprId - APR identifier. Pass null to suspend the fetch.
 * @param start - yyyy-mm-dd start date string (inclusive).
 * @param end - yyyy-mm-dd end date string (inclusive).
 * @returns SWR response with a `DailyKPIRecord[]` array.
 */
export function useDailyKpis(
  aprId: string | null,
  start: string | null,
  end: string | null,
) {
  const key =
    aprId && start && end
      ? `${API_BASE}/kpis/daily${qs({ apr_id: aprId, start, end })}`
      : null;
  return useSWR<DailyKPIRecord[]>(key, fetcher, SWR_CONFIG);
}
