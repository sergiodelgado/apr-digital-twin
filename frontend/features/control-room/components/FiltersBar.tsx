"use client";

import type { Filters } from "@/features/aprs/types";

export function FiltersBar({
  filters,
  bounds,
  onChange,
}: {
  filters: Filters;
  bounds: { min: string; max: string } | null;
  onChange: (next: Filters) => void;
}) {
  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl border border-border bg-surface/80 p-4 backdrop-blur">
      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-muted">Desde</span>
        <input
          type="date"
          value={filters.startDate}
          min={bounds?.min}
          max={filters.endDate || bounds?.max}
          onChange={(e) => onChange({ ...filters, startDate: e.target.value })}
          className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-foreground outline-none focus:border-sky-500 [color-scheme:dark]"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-muted">Hasta</span>
        <input
          type="date"
          value={filters.endDate}
          min={filters.startDate || bounds?.min}
          max={bounds?.max}
          onChange={(e) => onChange({ ...filters, endDate: e.target.value })}
          className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-foreground outline-none focus:border-sky-500 [color-scheme:dark]"
        />
      </label>

      {bounds ? (
        <p className="ml-auto text-xs text-muted">
          Cobertura de datos: {bounds.min} → {bounds.max}
        </p>
      ) : null}
    </div>
  );
}
