// Pure type-only reference so svelte-check (which type-checks src/**/*.ts but
// not the root-level vitest-setup.ts runtime setup file) still sees jest-dom's
// matcher augmentation of vitest's Assertion interface (toBeInTheDocument,
// toHaveTextContent, etc.) used throughout src/**/__tests__/*.test.ts.
/// <reference types="@testing-library/jest-dom/vitest" />
