<script lang="ts">
	let {
		label = 'Actions',
		actions
	}: {
		label?: string;
		actions: { label: string; onclick: () => void; variant?: 'default' | 'danger' }[];
	} = $props();

	let open = $state(false);
	let triggerEl = $state<HTMLButtonElement | undefined>();
	let menuEl = $state<HTMLDivElement | undefined>();
	let menuStyle = $state('');

	// Rows live inside Table's overflow-x-auto wrapper - per the CSS overflow
	// spec, setting overflow-x alone still computes overflow-y to auto too,
	// so a menu positioned relative to its row (the natural approach) gets
	// silently clipped by the table's own bottom edge for any row near the
	// end of the list. Positioning it via `fixed` + a portal to <body>
	// escapes that clipping ancestor entirely.
	function positionMenu() {
		if (!triggerEl) return;
		const rect = triggerEl.getBoundingClientRect();
		menuStyle = `position: fixed; top: ${rect.bottom + 4}px; right: ${window.innerWidth - rect.right}px;`;
	}

	function toggle() {
		if (open) {
			open = false;
			return;
		}
		positionMenu();
		open = true;
	}

	function handleWindowClick(event: MouseEvent) {
		if (!open) return;
		const target = event.target as Node;
		if (triggerEl?.contains(target) || menuEl?.contains(target)) return;
		open = false;
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') open = false;
	}

	function trigger(action: { onclick: () => void }) {
		open = false;
		action.onclick();
	}

	// Moves the menu's DOM node to <body> on mount so `position: fixed`
	// above is relative to the viewport, not the (clipped) Table ancestor.
	function portal(node: HTMLElement) {
		document.body.appendChild(node);
		return {
			destroy() {
				node.remove();
			}
		};
	}
</script>

<svelte:window
	onclick={handleWindowClick}
	onkeydown={open ? handleKeydown : undefined}
	onscroll={open ? () => (open = false) : undefined}
/>

<button
	bind:this={triggerEl}
	type="button"
	onclick={toggle}
	aria-haspopup="menu"
	aria-expanded={open}
	aria-label={label}
	class="rounded-card px-2 py-1 text-lg leading-none text-slate-500 hover:bg-slate-100 hover:text-text focus:outline-none focus:ring-1 focus:ring-primary"
>
	&#8942;
</button>

{#if open}
	<div use:portal bind:this={menuEl} role="menu" style={menuStyle} class="z-50">
		<div
			class="min-w-[8rem] rounded-card border border-slate-200 bg-surface py-1 shadow-card"
		>
			{#each actions as action (action.label)}
				<button
					type="button"
					role="menuitem"
					onclick={() => trigger(action)}
					class="block w-full px-3 py-1.5 text-left text-sm hover:bg-slate-100 {action.variant ===
					'danger'
						? 'text-red-700'
						: 'text-text'}"
				>
					{action.label}
				</button>
			{/each}
		</div>
	</div>
{/if}
