<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		open = $bindable(false),
		title,
		children
	}: {
		open?: boolean;
		title?: string;
		children: Snippet;
	} = $props();

	const uid = $props.id();
	const titleId = `${uid}-title`;

	function close() {
		open = false;
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') close();
	}

	function handleBackdropClick(event: MouseEvent) {
		// Only the backdrop itself should close - clicks inside the dialog
		// bubble up here too, but their target won't be currentTarget.
		if (event.target === event.currentTarget) close();
	}
</script>

<svelte:window onkeydown={open ? handleKeydown : undefined} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
		onclick={handleBackdropClick}
		role="presentation"
	>
		<div
			class="w-full max-w-sm rounded-card bg-surface p-6 shadow-card"
			role="dialog"
			tabindex="-1"
			aria-modal="true"
			aria-labelledby={title ? titleId : undefined}
		>
			<div class="mb-4 flex items-center justify-between">
				{#if title}
					<h2 id={titleId} class="text-lg font-semibold text-text">{title}</h2>
				{/if}
				<button
					type="button"
					class="text-slate-500 hover:text-text"
					onclick={close}
					aria-label="Close"
				>
					✕
				</button>
			</div>
			{@render children()}
		</div>
	</div>
{/if}
