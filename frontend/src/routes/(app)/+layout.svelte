<script lang="ts">
	import { isAuthenticated, isLoading, login } from '$lib/auth';

	let { children } = $props();

	// Every route under this group requires auth: while loading, render
	// nothing meaningful; once resolved, redirect unauthenticated visitors to
	// Auth0 login instead of rendering the page.
	$effect(() => {
		if (!$isLoading && !$isAuthenticated) login();
	});
</script>

{#if $isLoading}
	<p class="text-sm text-slate-500">Loading...</p>
{:else if $isAuthenticated}
	{@render children?.()}
{/if}
