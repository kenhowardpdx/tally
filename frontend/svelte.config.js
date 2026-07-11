import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// fallback: 'index.html' makes this a true client-routed SPA (S3's
		// error_document already serves index.html for any unknown path - see
		// infra/modules/frontend_s3/main.tf) instead of relying on prerendering
		// every route, which breaks for dynamic routes like /accounts/[id].
		adapter: adapter({ fallback: 'index.html' })
	}
};

export default config;
