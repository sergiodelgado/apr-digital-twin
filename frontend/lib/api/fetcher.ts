/**
 * Fetches data from a REST API endpoint and returns it as a JSON object.
 * @param url - The API endpoint URL.
 * @returns A promise resolving to the fetched data.
 */
export async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url);

  if (!res.ok) throw new Error(`API error ${res.status}: ${url}`);

  return await res.json() as Promise<T>;
}

/**
 * Shared SWR configuration applied to all API data hooks.
 * Disables focus revalidation and caps retries to keep API outages visible and recoverable.
 */
export const SWR_CONFIG = {
  revalidateOnFocus: false,
  errorRetryCount: 2,
  errorRetryInterval: 3000,
  shouldRetryOnError: true,
} as const;

/**
 * Converts an object of query parameters into a URL query string.
 * @param params - An object where keys are parameter names and values are parameter values.
 * @returns A URL query string.
 */
export function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value));
  }

  const str = search.toString();

  return str ? `?${str}` : '';
}
