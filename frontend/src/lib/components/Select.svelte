<script lang="ts">
	import Tooltip from '$lib/components/Tooltip.svelte';

	let {
		label,
		value = $bindable(''),
		id,
		options,
		tooltip
	}: {
		label?: string;
		value?: string;
		id?: string;
		options: { value: string; label: string }[];
		tooltip?: string;
	} = $props();

	const selectId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

	let open = $state(false);
	let containerEl = $state<HTMLDivElement | undefined>();
	let optionEls: (HTMLButtonElement | undefined)[] = [];

	const selectedLabel = $derived(options.find((o) => o.value === value)?.label ?? '');

	function pick(optionValue: string) {
		value = optionValue;
		open = false;
	}

	function focusOption(index: number) {
		optionEls[index]?.focus();
	}

	function openAndFocusSelected() {
		open = true;
		const selectedIndex = options.findIndex((o) => o.value === value);
		// Wait for the {#if open} popover to mount before focusing into it.
		requestAnimationFrame(() => focusOption(selectedIndex >= 0 ? selectedIndex : 0));
	}

	function handleWindowClick(event: MouseEvent) {
		if (open && containerEl && !containerEl.contains(event.target as Node)) {
			open = false;
		}
	}

	// Roving focus among the option buttons, matching the WAI-ARIA listbox
	// pattern implied by role="listbox"/role="option" below - without this,
	// a keyboard user could only Tab through options one at a time with no
	// arrow-key navigation, unlike the native <select> this replaced.
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			open = false;
			return;
		}
		if (!open) return;
		const currentIndex = optionEls.findIndex((el) => el === document.activeElement);
		if (event.key === 'ArrowDown') {
			event.preventDefault();
			focusOption(currentIndex < options.length - 1 ? currentIndex + 1 : 0);
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			focusOption(currentIndex > 0 ? currentIndex - 1 : options.length - 1);
		} else if (event.key === 'Home') {
			event.preventDefault();
			focusOption(0);
		} else if (event.key === 'End') {
			event.preventDefault();
			focusOption(options.length - 1);
		}
	}
</script>

<svelte:window onclick={handleWindowClick} onkeydown={open ? handleKeydown : undefined} />

<div class="relative flex flex-col gap-1" bind:this={containerEl}>
	{#if label}
		<label for={selectId} class="flex items-center text-sm font-medium text-text">
			{label}
			{#if tooltip}
				<Tooltip text={tooltip} />
			{/if}
		</label>
	{/if}
	<button
		type="button"
		id={selectId}
		onclick={() => (open ? (open = false) : openAndFocusSelected())}
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
			{#each options as option, i (option.value)}
				<button
					type="button"
					role="option"
					aria-selected={option.value === value}
					bind:this={optionEls[i]}
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
