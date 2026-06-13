import useSWR from 'swr';
import { fetcher, qs, SWR_CONFIG } from '@/lib/api/fetcher';
import { API_BASE } from '@/lib/constants';
import type { TwinState } from '@/lib/types';

/**
 * SWR hook that fetches the current digital twin state for a given APR.
 * Suspends the request (null key) when aprId is null.
 * Revalidation on focus is disabled to avoid noise during operational monitoring.
 *
 * @param aprId - APR identifier, or null to suspend the fetch.
 * @returns SWR response with a `TwinState` object.
 */
export function useTwinState(aprId: string | null) {
  return useSWR<TwinState>(
    aprId ? `${API_BASE}/twin/state${qs({ apr_id: aprId })}` : null,
    fetcher,
    SWR_CONFIG,
  );
}
