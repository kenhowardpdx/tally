<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<div class="rounded-card bg-surface p-6 shadow-card">
	{@render children()}
</div>
