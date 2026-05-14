import { describe, it, expect, beforeEach } from 'vitest'
import { setupHarness } from '../helpers/harness.js'

describe('smoke: truncatePrefix', () => {
  let dts
  beforeEach(() => {
    dts = setupHarness()
  })

  it('returns the prefix unchanged for levelsUp <= 0', () => {
    expect(dts.truncatePrefix('orders-2-items-3-', 0)).toBe('orders-2-items-3-')
    expect(dts.truncatePrefix('orders-2-items-3-', -1)).toBe('orders-2-items-3-')
  })

  it('walks back one formset segment for levelsUp=1', () => {
    expect(dts.truncatePrefix('orders-2-items-3-', 1)).toBe('orders-2-')
  })

  it('returns empty string for equal-depth (valid top-level case)', () => {
    expect(dts.truncatePrefix('orders-2-items-3-', 2)).toBe('')
  })

  it('degrades unchanged for misconfig (levelsUp > segments)', () => {
    expect(dts.truncatePrefix('orders-2-items-3-', 3)).toBe('orders-2-items-3-')
    expect(dts.truncatePrefix('orders-2-items-3-', 99)).toBe('orders-2-items-3-')
  })

  it('handles hyphenated formset names by counting -\\d+- boundaries only', () => {
    // The `-line-` segment has no numeric index and must not be treated as a
    // formset boundary. Anchor is /-\d+-/g, same as applyIndices.
    expect(dts.truncatePrefix('orders-2-line-items-3-', 1)).toBe('orders-2-')
  })

  it('handles single-level parent-reference (formset to top-level form field)', () => {
    expect(dts.truncatePrefix('formset-0-', 1)).toBe('')
  })

  it('returns unchanged for single-level prefix when asked to walk above top', () => {
    expect(dts.truncatePrefix('formset-0-', 2)).toBe('formset-0-')
  })

  it('handles empty prefix with any levelsUp', () => {
    // No segments + levelsUp > 0 falls into the misconfig branch -> unchanged ''.
    expect(dts.truncatePrefix('', 1)).toBe('')
    expect(dts.truncatePrefix('', 0)).toBe('')
  })

  it('treats levelsUp=undefined like zero', () => {
    // createFirstUrlFunction passes `filter.levelsUp || 0`; harness-level
    // robustness against the same undefined input is worth pinning.
    expect(dts.truncatePrefix('orders-2-items-3-', undefined)).toBe('orders-2-items-3-')
  })
})
