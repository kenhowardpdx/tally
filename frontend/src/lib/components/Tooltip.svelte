<script lang="ts">
	let { text, id }: { text: string; id?: string } = $props();

	const tooltipId = id ?? `tooltip-${Math.random().toString(36).slice(2, 9)}`;
	const width = 224; // matches w-56
	const gap = 8; // matches mb-2/mt-2

	let triggerEl = $state<HTMLButtonElement | undefined>();
	let visible = $state(false);
	let style = $state('');

	// Tooltips render inside tables/lists with an overflow-x-auto wrapper
	// (see Table.svelte), which clips anything positioned relative to a row
	// once it crosses the wrapper's edge. Portaling to <body> with
	// `position: fixed` computed from the trigger's own rect escapes that
	// clipping ancestor entirely - the same approach RowActionsMenu uses for
	// its dropdown.
	function position() {
		if (!triggerEl) return;
		const rect = triggerEl.getBoundingClientRect();

		let left = rect.left + rect.width / 2 - width / 2;
		left = Math.max(8, Math.min(left, window.innerWidth - width - 8));

		// Flips below the trigger when there isn't room above, so the
		// tooltip doesn't render off the top of the viewport either.
		if (rect.top < 80) {
			style = `left: ${left}px; top: ${rect.bottom + gap}px; width: ${width}px;`;
		} else {
			style = `left: ${left}px; bottom: ${window.innerHeight - rect.top + gap}px; width: ${width}px;`;
		}
	}

	function show() {
		position();
		visible = true;
	}

	function hide() {
		visible = false;
	}

	// Moves the tooltip's DOM node to <body> on mount so `position: fixed`
	// above is relative to the viewport, not a (potentially clipping)
	// ancestor.
	function portal(node: HTMLElement) {
		document.body.appendChild(node);
		return {
			destroy() {
				node.remove();
			}
		};
	}
</script>

<svelte:window onscroll={visible ? hide : undefined} onresize={visible ? position : undefined} />

<span class="relative inline-flex">
	<button
		bind:this={triggerEl}
		type="button"
		aria-describedby={tooltipId}
		onpointerenter={show}
		onpointerleave={hide}
		onfocus={show}
		onblur={hide}
		class="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-slate-200 text-[10px] font-semibold text-slate-600 hover:bg-slate-300 focus:outline-none focus:ring-2 focus:ring-primary"
	>
		?
	</button>
	<span
		use:portal
		id={tooltipId}
		role="tooltip"
		style="position: fixed; {style}"
		class="pointer-events-none z-50 rounded-card bg-text px-3 py-2 text-xs font-normal text-white shadow-card {visible
			? 'block'
			: 'hidden'}"
	>
		{text}
	</span>
</span>
