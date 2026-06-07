"use client";

import type { SummaryMetric } from "@/lib/telemetry";
import { Metric } from "./ui/primitives";

export function ExecutiveSummary({ metrics }: { metrics: SummaryMetric[] }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((m) => (
        <Metric
          key={m.label}
          label={m.label}
          value={m.value}
          detail={m.detail}
          tone={m.tone}
        />
      ))}
    </div>
  );
}
