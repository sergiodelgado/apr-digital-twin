// Helpers de formato en español (fechas, números).
import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "N/D";
  try {
    return format(parseISO(value), "dd MMM yyyy HH:mm", { locale: es });
  } catch {
    return "N/D";
  }
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "N/D";
  try {
    return format(parseISO(value), "dd MMM yyyy", { locale: es });
  } catch {
    return "N/D";
  }
}

export function formatNumber(
  value: number | null | undefined,
  digits = 1,
  unit = "",
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/D";
  const formatted = value.toLocaleString("es-CL", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return unit ? `${formatted} ${unit}` : formatted;
}

export function formatPercent(ratio: number | null | undefined, digits = 1): string {
  if (ratio === null || ratio === undefined || Number.isNaN(ratio)) return "N/D";
  return `${(ratio * 100).toFixed(digits)}%`;
}
