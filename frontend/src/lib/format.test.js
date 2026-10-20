import { describe, it, expect } from 'vitest';
import { formatDate, formatDateShort, formatTime, formatPrice, initials } from './format';

describe('formatDate', () => {
  it('formats an ISO string as a readable date', () => {
    expect(formatDate('2027-03-05T18:00:00Z')).toMatch(/Mar 5, 2027/);
  });

  it('returns an empty string for falsy input', () => {
    expect(formatDate(null)).toBe('');
    expect(formatDate(undefined)).toBe('');
  });
});

describe('formatDateShort', () => {
  it('splits into an uppercase month and a day number', () => {
    const { month, day } = formatDateShort('2027-07-04T12:00:00Z');
    expect(month).toBe('JUL');
    expect(day).toBe('4');
  });

  it('returns an empty string for falsy input', () => {
    expect(formatDateShort(null)).toBe('');
  });
});

describe('formatTime', () => {
  it('formats an ISO string as a time', () => {
    expect(formatTime('2027-01-01T04:30:00Z')).toMatch(/:\d{2}\s?(AM|PM)/);
  });

  it('returns an empty string for falsy input', () => {
    expect(formatTime(undefined)).toBe('');
  });
});

describe('formatPrice', () => {
  it('renders "Free" for zero or missing amounts', () => {
    expect(formatPrice(0)).toBe('Free');
    expect(formatPrice(null)).toBe('Free');
    expect(formatPrice(undefined)).toBe('Free');
    expect(formatPrice(-5)).toBe('Free');
  });

  it('formats a positive amount as currency', () => {
    expect(formatPrice(42.5, 'USD')).toBe('$42.50');
  });

  it('respects a non-default currency', () => {
    expect(formatPrice(10, 'EUR')).toContain('10');
  });

  it('falls back gracefully for an invalid currency code', () => {
    expect(formatPrice(10, 'NOTREAL')).toBe('10.00 NOTREAL');
  });
});

describe('initials', () => {
  it('takes the first letter of up to two words', () => {
    expect(initials('Jane Doe')).toBe('JD');
  });

  it('handles a single word', () => {
    expect(initials('Cher')).toBe('C');
  });

  it('ignores extra whitespace between words', () => {
    expect(initials('  Jane   Doe  Smith')).toBe('JD');
  });

  it('handles an empty name', () => {
    expect(initials('')).toBe('');
  });
});
