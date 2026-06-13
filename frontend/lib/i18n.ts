/**
 * Shared Spanish (ES-CL) display labels for enum types defined in `lib/types.ts`.
 * Feature-specific translations live in `features/twin-state/lib/i18n.ts`.
 */
import type { Severity } from './types';

/** Maps Severity values to Spanish display labels used across multiple features. */
export const SEVERITY_ES: Record<Severity, string> = {
  OK: 'OK',
  WARNING: 'Advertencia',
  CRITICAL: 'Crítica',
};
