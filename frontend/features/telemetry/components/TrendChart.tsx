'use client';

import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card } from '@/components/ui/primitives';
import type { ChartPoint } from '../types';

/** A named horizontal reference line rendered as a dashed overlay inside TrendChart. */
export interface Threshold {
  value: number;
  /** Short Spanish label shown at the right edge of the reference line. */
  label: string;
  /** Hex or CSS color string for the line stroke and label. */
  color: string;
}

/**
 * Responsive Recharts line chart for a single telemetry metric over time.
 *
 * Renders threshold reference lines as dashed overlays and shows a no-data placeholder
 * when the selected time window contains no readings for the requested data key.
 * Animation is disabled for performance on large datasets.
 *
 * @param title - Human-readable chart label used in the heading and tooltip formatter.
 * @param data - Downsampled chart points produced by `buildChartSeries`.
 * @param dataKey - Metric to plot: "pressure", "tank", or "turbidity".
 * @param color - Hex/CSS color for the series line stroke.
 * @param unit - Physical unit appended in tooltip values (e.g. "bar", "%", "NTU").
 * @param thresholds - Optional operational thresholds to overlay as dashed reference lines.
 */
export function TrendChart({
  title,
  data,
  dataKey,
  color,
  unit,
  thresholds = [],
}: {
  title: string;
  data: ChartPoint[];
  dataKey: 'pressure' | 'tank' | 'turbidity';
  color: string;
  unit: string;
  thresholds?: Threshold[];
}) {
  const hasData = data.some((d) => d[dataKey] !== null);

  return (
    <Card>
      <h3 className="mb-3 text-base font-semibold text-foreground">{title}</h3>
      {!hasData ? (
        <p className="py-12 text-center text-sm text-muted">
          Sin telemetría disponible en el rango seleccionado.
        </p>
      ) : (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#243149"/>
              <XAxis dataKey="label" tick={{ fill: '#93a4c3', fontSize: 11 }} minTickGap={48} stroke="#243149"/>
              <YAxis tick={{ fill: '#93a4c3', fontSize: 11 }} stroke="#243149" width={48}/>
              <Tooltip
                contentStyle={{ background: '#111a2e', border: '1px solid #243149', borderRadius: 8, color: '#e8eef9' }}
                labelStyle={{ color: '#93a4c3' }}
                formatter={(value) => {
                  const num = typeof value === 'number' ? value : Number(value);
                  return [`${num.toFixed(2)} ${unit}`, title];
                }}
              />
              {thresholds.map((th) => (
                <ReferenceLine
                  key={th.label}
                  y={th.value}
                  stroke={th.color}
                  strokeDasharray="6 4"
                  label={{ value: th.label, position: 'right', fill: th.color, fontSize: 10 }}
                />
              ))}
              <Line
                type="monotone"
                dataKey={dataKey}
                stroke={color}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
