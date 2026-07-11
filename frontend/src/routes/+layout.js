// Fully client-side SPA (see svelte.config.js's fallback: 'index.html') -
// Auth0 auth state and all data come from client-side fetches, so there's
// nothing meaningful to prerender or server-render.
export const prerender = false;
export const ssr = false;
