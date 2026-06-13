import { describe, expect, it } from 'vitest';
import { SWR_CONFIG, qs } from '@/lib/api/fetcher';
import { REASON_CODE_ES } from '@/features/twin-state/lib/i18n';

describe('API helpers', () => {
  it('limits automatic retries for operational API failures', () => {
    expect(SWR_CONFIG.revalidateOnFocus).toBe(false);
    expect(SWR_CONFIG.errorRetryCount).toBe(2);
    expect(SWR_CONFIG.errorRetryInterval).toBe(3000);
  });

  it('builds encoded query strings and skips empty values', () => {
    expect(qs({ apr_id: 'APR 001', start: '', limit: 50 })).toBe(
      '?apr_id=APR+001&limit=50',
    );
  });
});

describe('reason-code translations', () => {
  it.each([
    'HYDRAULIC_PUMP_ON_NO_RECOVERY',
    'HYDRAULIC_ABNORMAL_TANK_DROP_RATE',
    'HYDRAULIC_LOW_PRESSURE_WITH_NORMAL_STORAGE',
    'HYDRAULIC_PROJECTED_DEPLETION_INSUFFICIENT_RECOVERY',
    'HYDRAULIC_TANK_SENSOR_ERRATIC',
    'PRESSURE_COMPLIANCE_BELOW_TARGET',
    'DATA_COMPLETENESS_AT_RISK',
  ])('translates %s', (code) => {
    expect(REASON_CODE_ES[code]).toBeTruthy();
  });
});
