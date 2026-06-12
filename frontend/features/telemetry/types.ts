import type { Severity } from "@/lib/types";

export type { Severity };

export interface ChartPoint {
  t: number;       // epoch ms
  label: string;   // readable axis label
  pressure: number | null;
  tank: number | null;
  turbidity: number | null;
}

export interface Incident {
  timestamp: string;
  event: string;
  severity: Severity;
  observedValue: string;
  threshold: string;
}
