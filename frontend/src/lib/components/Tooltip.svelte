<script lang="ts">
	let { text, id }: { text: string; id?: string } = $props();

	const tooltipId = id ?? `tooltip-${Math.random().toString(36).slice(2, 9)}`;
</script>

<span class="group relative inline-flex">
	<button
		type="button"
		aria-describedby={tooltipId}
		class="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-slate-200 text-[10px] font-semibold text-slate-600 hover:bg-slate-300 focus:outline-none focus:ring-2 focus:ring-primary"
	>
		?
	</button>
	<span
		id={tooltipId}
		role="tooltip"
		class="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 hidden w-56 -translate-x-1/2 rounded-card bg-text px-3 py-2 text-xs font-normal text-white shadow-card group-hover:block group-focus-within:block"
	>
		{text}
	</span>
</span>
