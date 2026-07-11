<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<div class="overflow-x-auto rounded-card border border-slate-200 bg-surface shadow-card">
	<table class="w-full text-left text-sm">
		{@render children()}
	</table>
</div>
