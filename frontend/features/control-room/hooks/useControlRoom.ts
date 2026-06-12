import { useEffect, useMemo, useState } from "react";
import { useAvailableAprs } from "@/features/aprs/hooks/useAvailableAprs";
import { dateBoundsFor, type Filters } from "@/features/aprs/types";
import { useTelemetry, useDailyKpis } from "@/features/telemetry/hooks";
import { useTwinState } from "@/features/twin-state/hooks/useTwinState";
import { buildAlertSummaries, buildExecutiveSummary } from "@/features/twin-state/lib/transform";
import { buildChartSeries, buildIncidents } from "@/features/telemetry/lib/transform";

export function useControlRoom(aprId: string) {
  const { data: aprs } = useAvailableAprs();
  const [filters, setFilters] = useState<Filters>({
    aprId,
    startDate: "",
    endDate: "",
  });

  // Initialize date bounds once APR catalog is available.
  useEffect(() => {
    if (!aprs || filters.startDate) return;
    const selected = aprs.find((a) => a.apr_id === aprId);
    const bounds = dateBoundsFor(selected);
    if (bounds) setFilters((f) => ({ ...f, startDate: bounds.min, endDate: bounds.max }));
  }, [aprs, aprId, filters.startDate]);

  const bounds = dateBoundsFor(aprs?.find((a) => a.apr_id === aprId));

  function handleFilterChange(next: Filters) {
    setFilters(next);
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
