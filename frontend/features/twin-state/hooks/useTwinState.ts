import useSWR from "swr";
import { fetcher, qs } from "@/lib/api/fetcher";
import { API_BASE } from "@/lib/constants";
import type { TwinState } from "@/lib/types";

export function useTwinState(aprId: string | null) {
  return useSWR<TwinState>(
    aprId ? `${API_BASE}/twin/state${qs({ apr_id: aprId })}` : null,
    fetcher,
    { revalidateOnFocus: false },
  );
}
