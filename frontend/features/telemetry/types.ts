import type { Severity } from '@/lib/types';

export type { Severity };

/** A single (possibly downsampled) data point used by the time-series charts. */
export interface ChartPoint {
  /** Epoch milliseconds — used as the Recharts x-axis key. */
  t: number;
  /** Human-readable axis label formatted as "DD/MM HH:MM". */
  label: string;
  pressure: number | null;
  tank: number | null;
  turbidity: number | null;
}

/** A single threshold-crossing event derived from raw telemetry records. */
export interface Incident {
  timestamp: string;
  /** Short Spanish event name displayed in the incidents table. */
  event: string;
  severity: Severity;
  /** Formatted observed sensor value at the time of the event. */
  observedValue: string;
  /** Formatted threshold value that was violated. */
  threshold: string;
}
