<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading } from '$lib/auth';

	$effect(() => {
		if (!$isLoading && $isAuthenticated) goto('/accounts');
	});
</script>

{#if !$isLoading && !$isAuthenticated}
	<h1 class="text-2xl font-semibold text-text">Tally</h1>
	<p class="mt-2 text-slate-600">
		Track recurring bills and forecast your bank balance. Log in to get started.
	</p>
{/if}
