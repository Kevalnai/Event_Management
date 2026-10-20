import { describe, it, expect } from 'vitest';
import { isImageUrl } from './isUrl';

describe('isImageUrl', () => {
  it('accepts http and https URLs', () => {
    expect(isImageUrl('https://example.com/banner.png')).toBe(true);
    expect(isImageUrl('http://example.com/banner.png')).toBe(true);
  });

  it('rejects garbage values instead of trusting them as a background-image URL', () => {
    expect(isImageUrl('string')).toBe(false);
    expect(isImageUrl('not a url')).toBe(false);
  });

  it('rejects non-http(s) protocols', () => {
    expect(isImageUrl('javascript:alert(1)')).toBe(false);
    expect(isImageUrl('ftp://example.com/x.png')).toBe(false);
  });

  it('rejects empty/null/undefined', () => {
    expect(isImageUrl('')).toBe(false);
    expect(isImageUrl(null)).toBe(false);
    expect(isImageUrl(undefined)).toBe(false);
  });
});
