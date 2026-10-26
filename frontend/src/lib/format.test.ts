import { describe, expect, it } from 'vitest'
import { euro, pct, date } from './format'
describe('display contracts', () => {
  it('formats money without converting currencies', () => { expect(euro('1018.00')).toContain('1,018.00'); expect(euro('0')).toContain('0.00') })
  it('keeps losses and gains explicit', () => { expect(pct(-1.234)).toBe('-1.23%'); expect(pct(0)).toBe('+0.00%') })
  it('converts UNIX seconds, not milliseconds, in Berlin', () => { expect(date(1792742400)).toMatch(/2026/); expect(date('2026-10-22T23:30:00Z')).toMatch(/23 Oct 2026/) })
})
