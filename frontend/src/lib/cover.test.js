import { describe, it, expect } from 'vitest';
import { coverFor } from './cover';

describe('coverFor', () => {
  it('is deterministic for the same seed', () => {
    const a = coverFor('event-123');
    const b = coverFor('event-123');
    expect(a).toEqual(b);
  });

  it('returns a gradient class and a glyph', () => {
    const { gradient, glyph } = coverFor('some event title');
    expect(typeof gradient).toBe('string');
    expect(gradient.length).toBeGreaterThan(0);
    expect(typeof glyph).toBe('string');
    expect(glyph.length).toBeGreaterThan(0);
  });

  it('does not throw on an empty seed', () => {
    expect(() => coverFor('')).not.toThrow();
    expect(() => coverFor(undefined)).not.toThrow();
  });
});
