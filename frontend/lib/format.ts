/**
 * Spanish-language formatting helpers for dates and numbers.
 * Functions provide localized formatting for display in Spanish (es-CL).
 */
import {format, parseISO} from 'date-fns';
import {es} from 'date-fns/locale';

/**
 * Formats a date-time string into a human-readable format (e.g., "15 Mar 2024 14:30").
 * @param value - The date-time string to format.
 * @returns A formatted date-time string.
 */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return 'N/D';

  try {
    return format(parseISO(value), 'dd MMM yyyy HH:mm', {locale: es});
  } catch {
    return 'N/D';
  }
}

/**
 * Formats a date string into a human-readable format (e.g., "15 Mar 2024").
 * @param value - The date string to format.
 * @returns A formatted date string.
 */
export function formatDate(value: string | null | undefined): string {
  if (!value) return 'N/D';
  try {
    return format(parseISO(value), 'dd MMM yyyy', {locale: es});
  } catch {
    return 'N/D';
  }
}

/**
 * Formats a number with specified decimal places and an optional unit, using Spanish locale formatting.
 * @param value - The number to format.
 * @param digits - The number of decimal places.
 * @param unit - The unit of the number (e.g., "kg", "m").
 * @returns A formatted number string.
 */
export function formatNumber(
  value: number | null | undefined,
  digits = 1,
  unit = '',
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/D';

  const formatted = value.toLocaleString('es-CL', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

  return unit ? `${formatted} ${unit}` : formatted;
}

/**
 * Formats a ratio as a percentage string with specified decimal places, using Spanish locale formatting.
 * @param ratio - The ratio to format (e.g., 0.123 for 12.3%).
 * @param digits - The number of decimal places.
 * @returns A formatted percentage string.
 */
export function formatPercent(ratio: number | null | undefined, digits = 1): string {
  if (ratio === null || ratio === undefined || Number.isNaN(ratio)) return 'N/D';

  return `${(
    ratio * 100
  ).toFixed(digits)}%`;
}
