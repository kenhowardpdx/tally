import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/svelte';
import { afterEach } from 'vitest';

// @testing-library/svelte doesn't auto-register cleanup the way its React
// counterpart does under Vitest - without this, each render() in a test file
// leaks its DOM into the next test, breaking any getByRole/getByText query
// that expects exactly one match.
afterEach(() => cleanup());
