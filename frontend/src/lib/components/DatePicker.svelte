<script lang="ts">
	let {
		label,
		value = $bindable(''),
		id
	}: {
		label?: string;
		value?: string;
		id?: string;
	} = $props();

	const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
	const weekdayLabels = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

	let open = $state(false);
	let containerEl = $state<HTMLDivElement | undefined>();

	function parseISO(iso: string): Date | null {
		if (!iso) return null;
		const [y, m, d] = iso.split('-').map(Number);
		if (!y || !m || !d) return null;
		return new Date(y, m - 1, d);
	}

	function toISO(date: Date): string {
		const y = date.getFullYear();
		const m = String(date.getMonth() + 1).padStart(2, '0');
		const d = String(date.getDate()).padStart(2, '0');
		return `${y}-${m}-${d}`;
	}

	function isSameDay(a: Date | null, b: Date | null): boolean {
		return (
			!!a &&
			!!b &&
			a.getFullYear() === b.getFullYear() &&
			a.getMonth() === b.getMonth() &&
			a.getDate() === b.getDate()
		);
	}

	const selected = $derived(parseISO(value));

	let viewDate = $state(new Date());

	$effect(() => {
		if (selected) viewDate = new Date(selected.getFullYear(), selected.getMonth(), 1);
	});

	const monthLabel = $derived(
		viewDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
	);

	const weeks = $derived.by(() => {
		const year = viewDate.getFullYear();
		const month = viewDate.getMonth();
		const startOffset = new Date(year, month, 1).getDay();
		const daysInMonth = new Date(year, month + 1, 0).getDate();

		const cells: (Date | null)[] = [];
		for (let i = 0; i < startOffset; i++) cells.push(null);
		for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(year, month, d));
		while (cells.length % 7 !== 0) cells.push(null);

		const result: (Date | null)[][] = [];
		for (let i = 0; i < cells.length; i += 7) result.push(cells.slice(i, i + 7));
		return result;
	});

	function pick(date: Date) {
		value = toISO(date);
		open = false;
	}

	function prevMonth() {
		viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1);
	}

	function nextMonth() {
		viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1);
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
		<label for={inputId} class="text-sm font-medium text-text">{label}</label>
	{/if}
	<button
		type="button"
		id={inputId}
		onclick={() => (open = !open)}
		class="rounded-card border border-slate-300 px-3 py-2 text-left text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
	>
		{value || 'Select date'}
	</button>

	{#if open}
		<div
			class="absolute top-full z-10 mt-1 w-64 rounded-card border border-slate-200 bg-surface p-3 shadow-card"
		>
			<div class="mb-2 flex items-center justify-between">
				<button
					type="button"
					onclick={prevMonth}
					class="rounded px-2 py-1 text-sm text-slate-500 hover:bg-slate-100"
					aria-label="Previous month"
				>
					‹
				</button>
				<span class="text-sm font-medium text-text">{monthLabel}</span>
				<button
					type="button"
					onclick={nextMonth}
					class="rounded px-2 py-1 text-sm text-slate-500 hover:bg-slate-100"
					aria-label="Next month"
				>
					›
				</button>
			</div>
			<div class="grid grid-cols-7 gap-1 text-center text-xs text-slate-400">
				{#each weekdayLabels as day, i (i)}
					<span>{day}</span>
				{/each}
			</div>
			{#each weeks as week, weekIndex (weekIndex)}
				<div class="grid grid-cols-7 gap-1">
					{#each week as day, dayIndex (dayIndex)}
						{#if day}
							<button
								type="button"
								onclick={() => pick(day)}
								class="rounded px-1 py-1 text-sm hover:bg-slate-100 {isSameDay(day, selected)
									? 'bg-primary text-white hover:bg-primary/90'
									: 'text-text'}"
							>
								{day.getDate()}
							</button>
						{:else}
							<span></span>
						{/if}
					{/each}
				</div>
			{/each}
		</div>
	{/if}
</div>
