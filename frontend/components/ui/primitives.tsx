import type { ReactNode } from 'react';
import type { FreshnessStatus, Severity, SystemStatus } from '@/lib/types';

type Tone = Severity | 'INFO' | 'NEUTRAL';

/** Color classes (text + background + border) indexed by tone, used in Badge and accent elements. */
const TONE_BADGE: Record<Tone, string> = {
  OK: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  WARNING: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  CRITICAL: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  INFO: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  NEUTRAL: 'bg-slate-500/15 text-slate-300 border-slate-500/30',
};

/**
 * Base glassmorphism card container with a subtle border, surface background, and drop shadow.
 * @param children - Card content.
 * @param className - Additional Tailwind classes to merge with the base styles.
 */
export function Card({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-border bg-surface/80 p-4 shadow-lg shadow-black/20 backdrop-blur ${className}`}
    >
      {children}
    </div>
  );
}

/**
 * Semantic section wrapper with a two-line heading area and an optional right-aligned slot.
 * @param title - Primary section heading.
 * @param subtitle - Optional secondary line shown below the title.
 * @param children - Section body content.
 * @param right - Optional node rendered to the right of the heading (e.g., a badge or control).
 */
export function Section({
  title,
  subtitle,
  children,
  right,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  right?: ReactNode;
}) {
  return (
    <section className="space-y-3">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-foreground">{title}</h2>
          {subtitle ? <p className="text-sm text-muted">{subtitle}</p> : null}
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

/**
 * Pill-shaped status badge with tone-driven color styling.
 * @param children - Badge label content.
 * @param tone - Color tone applied to background, text, and border. Defaults to 'NEUTRAL'.
 * @param className - Additional Tailwind classes.
 */
export function Badge({
  children,
  tone = 'NEUTRAL',
  className = '',
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${TONE_BADGE[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

/**
 * KPI metric card with a label, large value, and optional detail line.
 * The value text color is driven by the tone prop.
 * @param label - Short metric name (rendered in uppercase tracking).
 * @param value - Primary metric value (may be a ReactNode for rich formatting).
 * @param detail - Optional secondary line shown below the value.
 * @param tone - Color tone applied to the value text. Defaults to 'NEUTRAL'.
 */
export function Metric({
  label,
  value,
  detail,
  tone = 'NEUTRAL',
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  tone?: Tone;
}) {
  const accent: Record<Tone, string> = {
    OK: 'text-emerald-300',
    WARNING: 'text-amber-300',
    CRITICAL: 'text-rose-300',
    INFO: 'text-sky-300',
    NEUTRAL: 'text-foreground',
  };
  return (
    <Card className="h-full">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${accent[tone]}`}>{value}</p>
      {detail ? <p className="mt-1 text-sm text-muted">{detail}</p> : null}
    </Card>
  );
}

/**
 * Maps a SystemStatus value to a display Tone for Badge and Metric components.
 * @param status - System-level operational status from the twin state.
 * @returns Corresponding Tone value.
 */
export function systemStatusTone(status: SystemStatus): Tone {
  switch (status) {
    case 'OK':
      return 'OK';
    case 'WARNING':
      return 'WARNING';
    case 'CRITICAL':
      return 'CRITICAL';
    default:
      return 'NEUTRAL';
  }
}

/**
 * Maps a FreshnessStatus value to a display Tone for Badge and Metric components.
 * @param freshness - Telemetry freshness classification from the twin state.
 * @returns Corresponding Tone value.
 */
export function freshnessTone(freshness: FreshnessStatus): Tone {
  switch (freshness) {
    case 'FRESH':
      return 'OK';
    case 'STALE':
      return 'WARNING';
    case 'OUTDATED':
      return 'CRITICAL';
    default:
      return 'NEUTRAL';
  }
}

/**
 * Identity mapping from Severity to Tone. Provided for API consistency across helper functions.
 * @param severity - Severity level.
 * @returns The same value cast as Tone.
 */
export function severityTone(severity: Severity): Tone {
  return severity;
}
