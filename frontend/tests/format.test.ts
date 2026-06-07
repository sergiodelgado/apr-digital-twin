import { describe, it, expect } from "vitest";
import {
  formatDateTime,
  formatDate,
  formatNumber,
  formatPercent,
} from "../lib/format";

describe("formatDateTime", () => {
  it("formats valid ISO strings correctly", () => {
    // We parse and format using es-CL locale, so "2026-06-07T12:00:00Z"
    // is expected to format containing day, month representation (jun) and year.
    const result = formatDateTime("2026-06-07T12:00:00Z");
    expect(result).toContain("07");
    expect(result).toContain("jun");
    expect(result).toContain("2026");
  });

  it("returns N/D for null, undefined, or empty values", () => {
    expect(formatDateTime(null)).toBe("N/D");
    expect(formatDateTime(undefined)).toBe("N/D");
    expect(formatDateTime("")).toBe("N/D");
  });

  it("returns N/D for invalid date strings", () => {
    expect(formatDateTime("invalid-date-string")).toBe("N/D");
  });
});

describe("formatDate", () => {
  it("formats valid ISO strings to date-only correctly", () => {
    const result = formatDate("2026-06-07T12:00:00Z");
    expect(result).toContain("07");
    expect(result).toContain("jun");
    expect(result).toContain("2026");
  });

  it("returns N/D for null, undefined, or empty values", () => {
    expect(formatDate(null)).toBe("N/D");
    expect(formatDate(undefined)).toBe("N/D");
    expect(formatDate("")).toBe("N/D");
  });

  it("returns N/D for invalid date strings", () => {
    expect(formatDate("invalid-date-string")).toBe("N/D");
  });
});

describe("formatNumber", () => {
  it("formats numbers with specified decimal digits and locale es-CL", () => {
    // es-CL uses "." as thousands separator and "," as decimal separator
    // In Node.js testing environment, locale support depends on the runner configuration,
    // but we can test formatting characteristics.
    const formatted = formatNumber(1234.56, 1);
    // Should be "1.234,6" or similar localized format (using comma as decimal or dot)
    // We check if it formats successfully with decimal digit limit
    expect(formatted).toMatch(/1[.,]234[.,]6/);
  });

  it("appends unit if provided", () => {
    const formatted = formatNumber(12.3, 1, "bar");
    expect(formatted).toContain("12");
    expect(formatted).toContain("bar");
  });

  it("returns N/D for null, undefined, and NaN", () => {
    expect(formatNumber(null)).toBe("N/D");
    expect(formatNumber(undefined)).toBe("N/D");
    expect(formatNumber(NaN)).toBe("N/D");
  });
});

describe("formatPercent", () => {
  it("formats ratios to percentages correctly", () => {
    expect(formatPercent(0.952, 1)).toBe("95.2%");
    expect(formatPercent(0.05, 0)).toBe("5%");
  });

  it("returns N/D for null, undefined, and NaN", () => {
    expect(formatPercent(null)).toBe("N/D");
    expect(formatPercent(undefined)).toBe("N/D");
    expect(formatPercent(NaN)).toBe("N/D");
  });
});
