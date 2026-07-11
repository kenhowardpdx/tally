<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		label,
		value = $bindable(''),
		id,
		required = false,
		children
	}: {
		label?: string;
		value?: string;
		id?: string;
		required?: boolean;
		children: Snippet;
	} = $props();

	const selectId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
</script>

<div class="flex flex-col gap-1">
	{#if label}
		<label for={selectId} class="text-sm font-medium text-text">{label}</label>
	{/if}
	<select
		id={selectId}
		{required}
		bind:value
		class="rounded-card border border-slate-300 px-3 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
	>
		{@render children()}
	</select>
</div>
