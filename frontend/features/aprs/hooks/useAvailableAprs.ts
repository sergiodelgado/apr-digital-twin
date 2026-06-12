import useSWR from "swr";
import { fetcher } from "@/lib/api/fetcher";
import { API_BASE } from "@/lib/constants";
import type { AvailableAPRRecord } from "@/lib/types";

export function useAvailableAprs() {
  return useSWR<AvailableAPRRecord[]>(
    `${API_BASE}/available_aprs`,
    fetcher,
    { revalidateOnFocus: false },
  );
}
