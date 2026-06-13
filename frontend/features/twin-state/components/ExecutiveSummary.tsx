'use client';

import { Metric } from '@/components/ui/primitives';
import type { SummaryMetric } from '../types';

/**
 * Responsive grid of Metric primitive cards showing key executive KPIs for the selected period.
 * Covers pressure compliance, tank risk, water-quality risk, and data completeness.
 *
 * @param metrics - Array of SummaryMetric objects produced by `buildExecutiveSummary`.
 */
export function ExecutiveSummary({ metrics }: { metrics: SummaryMetric[] }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((m) => (
        <Metric key={m.label} label={m.label} value={m.value} detail={m.detail} tone={m.tone} />
      ))}
    </div>
  );
}
