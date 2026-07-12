<script lang="ts">
	let {
		label,
		value = $bindable(''),
		id,
		required = false,
		options
	}: {
		label?: string;
		value?: string;
		id?: string;
		required?: boolean;
		options: { value: string; label: string }[];
	} = $props();

	const selectId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

	let open = $state(false);
	let containerEl = $state<HTMLDivElement | undefined>();

	const selectedLabel = $derived(options.find((o) => o.value === value)?.label ?? '');

	function pick(optionValue: string) {
		value = optionValue;
		open = false;
	}

	function handleWindowClick(event: MouseEvent) {
		if (open && containerEl && !containerEl.contains(event.target as Node)) {
			open = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') open = false;
	}
</script>

<svelte:window onclick={handleWindowClick} onkeydown={open ? handleKeydown : undefined} />

<div class="relative flex flex-col gap-1" bind:this={containerEl}>
	{#if label}
		<label for={selectId} class="text-sm font-medium text-text">{label}</label>
	{/if}
	<button
		type="button"
		id={selectId}
		onclick={() => (open = !open)}
		aria-haspopup="listbox"
		aria-expanded={open}
		class="flex items-center justify-between gap-2 rounded-card border border-slate-300 bg-surface px-3 py-2 text-left text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
	>
		<span>{selectedLabel || 'Select…'}</span>
		<span class="text-slate-400">▾</span>
	</button>

	{#if open}
		<div
			class="absolute top-full z-10 mt-1 w-full min-w-max rounded-card border border-slate-200 bg-surface py-1 shadow-card"
			role="listbox"
		>
			{#each options as option (option.value)}
				<button
					type="button"
					role="option"
					aria-selected={option.value === value}
					onclick={() => pick(option.value)}
					class="block w-full px-3 py-2 text-left text-sm hover:bg-slate-100 {option.value ===
					value
						? 'bg-slate-50 font-medium text-primary'
						: 'text-text'}"
				>
					{option.label}
				</button>
			{/each}
		</div>
	{/if}
</div>
