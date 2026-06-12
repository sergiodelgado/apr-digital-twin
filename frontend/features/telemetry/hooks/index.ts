import useSWR from "swr";
import { fetcher, qs } from "@/lib/api/fetcher";
import { API_BASE } from "@/lib/constants";
import type { DailyKPIRecord, TelemetryRecord } from "@/lib/types";

export function useTelemetry(
  aprId: string | null,
  start: string | null,
  end: string | null,
) {
  const key =
    aprId && start && end
      ? `${API_BASE}/telemetry/recent${qs({ apr_id: aprId, start, end, limit: 5000 })}`
      : null;
  return useSWR<TelemetryRecord[]>(key, fetcher, { revalidateOnFocus: false });
}

export function useDailyKpis(
  aprId: string | null,
  start: string | null,
  end: string | null,
) {
  const key =
    aprId && start && end
      ? `${API_BASE}/kpis/daily${qs({ apr_id: aprId, start, end })}`
      : null;
  return useSWR<DailyKPIRecord[]>(key, fetcher, { revalidateOnFocus: false });
}
