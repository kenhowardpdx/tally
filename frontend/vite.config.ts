import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig(({ mode }) => ({
	plugins: [tailwindcss(), sveltekit()],
	test: {
		environment: 'jsdom',
		setupFiles: ['./vitest-setup.ts'],
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	// Svelte 5's component-instantiation code path differs between the
	// browser and SSR/Node - without forcing the browser condition in the
	// test runner, mounting a component under jsdom hits the SSR path
	// instead (no client-side reactivity). Scoped to `mode === 'test'` only
	// so the actual dev server / production build (which need SvelteKit's
	// normal server/client condition split) are unaffected.
	resolve: {
		conditions: mode === 'test' ? ['browser'] : undefined
	}
}));
