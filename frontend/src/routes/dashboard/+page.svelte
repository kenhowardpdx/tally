<script lang="ts">
	import { apiFetch } from '$lib/api';
	import { isAuthenticated, isLoading, login } from '$lib/auth';

	// Protected route pattern: while auth state is loading, render nothing;
	// once resolved, redirect unauthenticated visitors to Auth0 login instead
	// of rendering the page. Every protected route follows this shape.
	$effect(() => {
		if (!$isLoading && !$isAuthenticated) login();
	});

	// Dev-only manual check that round-trips a real access token through the
	// backend's JWT validation - gated below so it never ships to real users.
	let meResult = $state<string | null>(null);
	async function checkBackendAuth() {
		meResult = 'Loading...';
		try {
			const res = await apiFetch('/api/v1/me');
			meResult = res.ok ? JSON.stringify(await res.json()) : `Error: HTTP ${res.status}`;
		} catch (err) {
			meResult = `Error: ${err instanceof Error ? err.message : String(err)}`;
		}
	}
</script>

{#if $isLoading}
	<p>Loading...</p>
{:else if $isAuthenticated}
	<h1>Dashboard</h1>
	<p>Signed in. Accounts and bills will live here (Phase 1).</p>

	{#if import.meta.env.DEV}
		<button onclick={checkBackendAuth}>Test backend auth (GET /api/v1/me)</button>
		{#if meResult}
			<pre>{meResult}</pre>
		{/if}
	{/if}
{/if}
