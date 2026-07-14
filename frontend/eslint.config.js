import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';

export default ts.config(
	js.configs.recommended,
	...ts.configs.recommended,
	...svelte.configs.recommended,
	{
		languageOptions: {
			globals: { ...globals.browser, ...globals.node }
		}
	},
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parserOptions: {
				parser: ts.parser
			}
		}
	},
	{
		rules: {
			// $props/$state/$derived etc. are compiler-injected in Svelte 5 runes
			// mode - not unused, not undefined, just invisible to plain ESLint.
			'no-unused-vars': 'off',
			'@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],

			// Requires routing every href/goto() through SvelteKit's typed
			// resolve() helper - a real migration worth doing deliberately across
			// ~20 call sites, not as a drive-by of turning linting on.
			'svelte/no-navigation-without-resolve': 'off',

			// Flags plain `new Date()` for one-off, non-reactive calculations
			// (e.g. computing a default end-date 90 days out) where the value is
			// never re-read after a mutation - SvelteDate exists for values whose
			// mutations need to trigger UI updates, which doesn't apply here.
			'svelte/prefer-svelte-reactivity': 'off'
		}
	},
	{
		ignores: ['build/', '.svelte-kit/', 'dist/', 'node_modules/']
	}
);
