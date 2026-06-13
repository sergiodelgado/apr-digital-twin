import type { Severity } from '@/lib/types';

export type { Severity };

/** Aggregated alert status for one monitored dimension (pressure, tank level, water quality, freshness). */
export interface AlertSummary {
  /** Stable dimension identifier used as a React key. */
  key: string;
  /** Spanish display title shown in the alert card. */
  title: string;
  /** True when the current twin state shows an active threshold violation. */
  activeNow: boolean;
  /** Number of distinct threshold-crossing event starts in the selected time window. */
  events: number;
  /** Worst severity level observed across all events in the window. */
  maxSeverity: Severity;
  /** Human-readable estimated duration of events (e.g. "12.5 min"). */
  durationLabel: string;
}

/** A single KPI metric row rendered in the executive summary grid. */
export interface SummaryMetric {
  /** Spanish metric label displayed in the card header. */
  label: string;
  /** Formatted primary value (e.g. "95.3%", "Bajo"). */
  value: string;
  /** Short Spanish contextual detail line rendered below the value. */
  detail: string;
  /** Severity tone driving the value text color. */
  tone: Severity;
}
