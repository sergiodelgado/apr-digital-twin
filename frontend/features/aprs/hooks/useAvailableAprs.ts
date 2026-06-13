import useSWR from 'swr';
import { fetcher, SWR_CONFIG } from '@/lib/api/fetcher';
import { API_BASE } from '@/lib/constants';
import type { AvailableAPRRecord } from '@/lib/types';

/**
 * SWR hook that fetches the full list of available APR records from the API catalog endpoint.
 * Revalidation on window focus is disabled to reduce unnecessary requests on the list page.
 *
 * @returns SWR response containing an `AvailableAPRRecord[]` array, plus `isLoading` and `error` state.
 */
export function useAvailableAprs() {
  return useSWR<AvailableAPRRecord[]>(
    `${API_BASE}/available_aprs`,
    fetcher,
    SWR_CONFIG,
  );
}
