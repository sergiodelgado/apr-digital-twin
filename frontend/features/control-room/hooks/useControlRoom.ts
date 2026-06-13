import { useMemo, useState } from 'react';
import { useAvailableAprs } from '@/features/aprs/hooks/useAvailableAprs';
import { dateBoundsFor, type Filters } from '@/features/aprs/types';
import { useDailyKpis, useTelemetry } from '@/features/telemetry/hooks';
import { useTwinState } from '@/features/twin-state/hooks/useTwinState';
import { buildAlertSummaries, buildExecutiveSummary } from '@/features/twin-state/lib/transform';
import { buildChartSeries, buildIncidents } from '@/features/telemetry/lib/transform';

/**
 * Orchestration hook for the APR control-room page.
 *
 * Coordinates twin state, telemetry, and KPI data fetching, and memoizes all
 * derived view data (chart series, incidents, alert summaries, executive metrics).
 * @param aprId - APR identifier taken from the URL route segment.
 * @returns All data and event handlers needed by ControlRoomView:
 *   - `filters` — Effective date range filters (user override or auto-derived bounds).
 *   - `bounds` — Available date range for the selected APR, or null while the catalog loads.
 *   - `twin` — Current twin state from the `/twin/state` endpoint.
 *   - `tel` — Raw telemetry records for the active window (empty array while loading).
 *   - `telLoading` — True while the telemetry request is in-flight.
 *   - `chartData` — Downsampled chart points produced by `buildChartSeries`.
 *   - `alertSummaries` — Four AlertSummary objects produced by `buildAlertSummaries`.
 *   - `execSummary` — Four SummaryMetric objects produced by `buildExecutiveSummary`.
 *   - `incidents` — Sorted, capped incident list produced by `buildIncidents`.
 *   - `handleFilterChange` — Callback to apply explicit user date overrides.
 */
export function useControlRoom(aprId: string) {
  const { data: aprs } = useAvailableAprs();

  /** Stores only the user's explicit date selections; empty strings mean "use bounds default". */
  const [userDates, setUserDates] = useState<{ startDate: string; endDate: string }>({
    startDate: '',
    endDate: '',
  });

  /** Available date range for the selected APR, memoized to avoid recomputing on every render. */
  const bounds = useMemo(
    () => dateBoundsFor(aprs?.find((a) => a.apr_id === aprId)),
    [aprs, aprId],
  );

  /**
   * Effective filters: user override takes priority; falls back to APR data bounds.
   * Computed during render — no useEffect, no extra render cycle.
   */
  const filters: Filters = useMemo(() => (
    {
      aprId,
      startDate: userDates.startDate || bounds?.min || '',
      endDate: userDates.endDate || bounds?.max || '',
    }
  ), [aprId, userDates, bounds]);

  /**
   * Stores the user's explicit date selection, overriding the automatic bounds defaults.
   * @param next - Updated Filters from the FiltersBar.
   */
  function handleFilterChange(next: Filters) {
    setUserDates({ startDate: next.startDate, endDate: next.endDate });
  }

  const telemetryStart = filters.startDate ? `${filters.startDate}T00:00:00` : null;
  const telemetryEnd = filters.endDate ? `${filters.endDate}T23:59:59` : null;

  const { data: twin } = useTwinState(aprId);
  const { data: telemetry, isLoading: telLoading } = useTelemetry(
    aprId,
    telemetryStart,
    telemetryEnd,
  );
  const { data: kpis } = useDailyKpis(aprId, filters.startDate || null, filters.endDate || null);

  const tel = useMemo(() => telemetry ?? [], [telemetry]);
  const gold = useMemo(() => kpis ?? [], [kpis]);

  const alertSummaries = useMemo(() => buildAlertSummaries(tel, gold, twin), [tel, gold, twin]);
  const execSummary = useMemo(() => buildExecutiveSummary(tel, gold, twin), [tel, gold, twin]);
  const incidents = useMemo(() => buildIncidents(tel), [tel]);
  const chartData = useMemo(() => buildChartSeries(tel), [tel]);

  return {
    filters,
    bounds,
    twin,
    tel,
    telLoading,
    chartData,
    alertSummaries,
    execSummary,
    incidents,
    handleFilterChange,
  };
}
