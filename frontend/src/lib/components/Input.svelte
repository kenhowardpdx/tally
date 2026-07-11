<script lang="ts">
	let {
		label,
		value = $bindable(''),
		type = 'text',
		placeholder,
		required = false,
		id
	}: {
		label?: string;
		value?: string;
		type?: string;
		placeholder?: string;
		required?: boolean;
		id?: string;
	} = $props();

	const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
</script>

<div class="flex flex-col gap-1">
	{#if label}
		<label for={inputId} class="text-sm font-medium text-text">{label}</label>
	{/if}
	<input
		id={inputId}
		{type}
		{placeholder}
		{required}
		bind:value
		class="rounded-card border border-slate-300 px-3 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
	/>
</div>
