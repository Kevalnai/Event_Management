import '@testing-library/jest-dom/vitest';

// jsdom has no IntersectionObserver; framer-motion's `whileInView` needs one.
class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.IntersectionObserver = MockIntersectionObserver;
