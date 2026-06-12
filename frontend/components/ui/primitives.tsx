// Primitivas de interfaz reutilizables para la sala de control (tema oscuro).
import type { ReactNode } from "react";
import type { FreshnessStatus, Severity, SystemStatus } from "@/lib/types";

type Tone = Severity | "INFO" | "NEUTRAL";

// Clases de color por tono (texto + fondo + borde) para badges y acentos.
const TONE_BADGE: Record<Tone, string> = {
  OK: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  WARNING: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  CRITICAL: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  INFO: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  NEUTRAL: "bg-slate-500/15 text-slate-300 border-slate-500/30",
};

export function Card({
  children,
  className = "",
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

export function Badge({
  children,
  tone = "NEUTRAL",
  className = "",
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

export function Metric({
  label,
  value,
  detail,
  tone = "NEUTRAL",
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  tone?: Tone;
}) {
  const accent: Record<Tone, string> = {
    OK: "text-emerald-300",
    WARNING: "text-amber-300",
    CRITICAL: "text-rose-300",
    INFO: "text-sky-300",
    NEUTRAL: "text-foreground",
  };
  return (
    <Card className="h-full">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${accent[tone]}`}>{value}</p>
      {detail ? <p className="mt-1 text-sm text-muted">{detail}</p> : null}
    </Card>
  );
}

// Mapea el estado del sistema a un tono de color.
export function systemStatusTone(status: SystemStatus): Tone {
  switch (status) {
    case "OK":
      return "OK";
    case "WARNING":
      return "WARNING";
    case "CRITICAL":
      return "CRITICAL";
    default:
      return "NEUTRAL";
  }
}

// Mapea la frescura de telemetría a un tono de color.
export function freshnessTone(freshness: FreshnessStatus): Tone {
  switch (freshness) {
    case "FRESH":
      return "OK";
    case "STALE":
      return "WARNING";
    case "OUTDATED":
      return "CRITICAL";
    default:
      return "NEUTRAL";
  }
}

export function severityTone(severity: Severity): Tone {
  return severity;
}
