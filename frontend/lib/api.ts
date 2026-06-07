// Fetchers y hooks SWR contra la API FastAPI a través del proxy same-origin
// /api/apr/* (ver next.config.ts). Todo el data fetching del front pasa por aquí.

import useSWR from "swr";
import { API_BASE } from "./constants";
import type {
  AvailableAPRRecord,
  DailyKPIRecord,
  TelemetryRecord,
  TwinState,
} from "./types";

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Error ${res.status} al consultar la API`);
  }
  return (await res.json()) as T;
}

function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const str = search.toString();
  return str ? `?${str}` : "";
}

// Catálogo de APRs disponibles (poblado desde Silver/Gold).
export function useAvailableAprs() {
  return useSWR<AvailableAPRRecord[]>(
    `${API_BASE}/available_aprs`,
    fetcher,
    { revalidateOnFocus: false },
  );
}

// Estado actual del gemelo para el APR seleccionado.
export function useTwinState(aprId: string | null) {
  return useSWR<TwinState>(
    aprId ? `${API_BASE}/twin/state${qs({ apr_id: aprId })}` : null,
    fetcher,
    { revalidateOnFocus: false },
  );
}

// Telemetría reciente (Silver) para tendencias, incidentes y vista cruda.
export function useTelemetry(
  aprId: string | null,
  start: string | null,
  end: string | null,
) {
  const key =
    aprId && start && end
      ? `${API_BASE}/telemetry/recent${qs({
          apr_id: aprId,
          start,
          end,
          limit: 5000,
        })}`
      : null;
  return useSWR<TelemetryRecord[]>(key, fetcher, { revalidateOnFocus: false });
}

// KPIs diarios (Gold) para el resumen ejecutivo y duraciones de alerta.
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
