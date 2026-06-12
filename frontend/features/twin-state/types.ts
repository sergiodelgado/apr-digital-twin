import type { Severity } from "@/lib/types";

export type { Severity };

export interface AlertSummary {
  key: string;
  title: string;
  activeNow: boolean;
  events: number;
  maxSeverity: Severity;
  durationLabel: string;
}

export interface SummaryMetric {
  label: string;
  value: string;
  detail: string;
  tone: Severity;
}
