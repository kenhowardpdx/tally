<script lang="ts">
	import { apiFetch } from '$lib/api';

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

<h1 class="text-2xl font-semibold text-text">Dashboard</h1>
<p class="mt-2 text-slate-600">
	Signed in. See <a class="text-primary underline" href="/accounts">Accounts</a> to manage bank
	accounts and bills.
</p>

{#if import.meta.env.DEV}
	<button
		class="mt-4 rounded-card border border-slate-300 px-3 py-1.5 text-sm text-text hover:bg-slate-50"
		onclick={checkBackendAuth}
	>
		Test backend auth (GET /api/v1/me)
	</button>
	{#if meResult}
		<pre class="mt-2 rounded-card bg-slate-100 p-3 text-xs">{meResult}</pre>
	{/if}
{/if}
