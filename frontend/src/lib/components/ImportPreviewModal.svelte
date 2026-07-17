<script lang="ts">
	import Button from './Button.svelte';
	import Modal from './Modal.svelte';

	// Presentational only - Bills/Transactions/Windfalls each format their own
	// rows into these plain-string summaries before passing them in, so this
	// component doesn't need to know anything about the three entity shapes.
	let {
		open = $bindable(false),
		title,
		newSummaries,
		updatedSummaries,
		unchangedCount,
		ambiguousMessages,
		omittedSummaries,
		// 'disable' (Bills/Windfalls - reversible, soft-delete) vs 'delete'
		// (Transactions - permanent) - controls the omitted section's styling
		// and whether an extra acknowledgement is required before confirming.
		omittedSeverity,
		confirming = false,
		onconfirm,
		oncancel
	}: {
		open: boolean;
		title: string;
		newSummaries: string[];
		updatedSummaries: string[];
		unchangedCount: number;
		ambiguousMessages: string[];
		omittedSummaries: string[];
		omittedSeverity: 'disable' | 'delete';
		confirming?: boolean;
		onconfirm: () => void;
		oncancel?: () => void;
	} = $props();

	let acknowledgedDeletion = $state(false);

	$effect(() => {
		if (open) acknowledgedDeletion = false;
	});

	const hasOmitted = $derived(omittedSummaries.length > 0);
	const requiresAcknowledgement = $derived(hasOmitted && omittedSeverity === 'delete');
	const canConfirm = $derived(
		!confirming && (!requiresAcknowledgement || acknowledgedDeletion)
	);
	const nothingToDo = $derived(
		newSummaries.length === 0 &&
			updatedSummaries.length === 0 &&
			omittedSummaries.length === 0 &&
			ambiguousMessages.length === 0
	);

	function close() {
		open = false;
		oncancel?.();
	}
</script>

<Modal bind:open {title}>
	<div class="flex max-h-[70vh] flex-col gap-4 overflow-y-auto text-sm">
		{#if nothingToDo}
			<p class="text-slate-600">Nothing to import - this file matches what's already here.</p>
		{/if}

		{#if newSummaries.length > 0}
			<div>
				<p class="font-medium text-emerald-700">{newSummaries.length} new</p>
				<ul class="mt-1 list-inside list-disc text-slate-600">
					{#each newSummaries as summary (summary)}
						<li>{summary}</li>
					{/each}
				</ul>
			</div>
		{/if}

		{#if updatedSummaries.length > 0}
			<div>
				<p class="font-medium text-primary">{updatedSummaries.length} updated</p>
				<ul class="mt-1 list-inside list-disc text-slate-600">
					{#each updatedSummaries as summary (summary)}
						<li>{summary}</li>
					{/each}
				</ul>
			</div>
		{/if}

		{#if unchangedCount > 0}
			<p class="text-slate-500">{unchangedCount} unchanged</p>
		{/if}

		{#if ambiguousMessages.length > 0}
			<div>
				<p class="font-medium text-amber-700">
					{ambiguousMessages.length} ambiguous - skipped, resolve manually
				</p>
				<ul class="mt-1 list-inside list-disc text-slate-600">
					{#each ambiguousMessages as message (message)}
						<li>{message}</li>
					{/each}
				</ul>
			</div>
		{/if}

		{#if hasOmitted}
			<div
				class="rounded-card border p-3 {omittedSeverity === 'delete'
					? 'border-red-200 bg-red-50'
					: 'border-slate-200 bg-slate-50'}"
			>
				<p class="font-medium {omittedSeverity === 'delete' ? 'text-red-700' : 'text-slate-700'}">
					{omittedSummaries.length}
					{omittedSeverity === 'delete'
						? 'will be permanently deleted'
						: 'not in this file - will be disabled'}
				</p>
				<ul class="mt-1 list-inside list-disc text-slate-600">
					{#each omittedSummaries as summary (summary)}
						<li>{summary}</li>
					{/each}
				</ul>
				{#if omittedSeverity === 'delete'}
					<label class="mt-3 flex items-start gap-2 text-red-700">
						<input type="checkbox" class="mt-0.5" bind:checked={acknowledgedDeletion} />
						<span>I understand this cannot be undone.</span>
					</label>
				{/if}
			</div>
		{/if}
	</div>

	<div class="mt-4 flex justify-end gap-2">
		<Button variant="secondary" onclick={close} disabled={confirming}>Cancel</Button>
		<Button onclick={onconfirm} disabled={!canConfirm || nothingToDo}>
			{confirming ? 'Importing…' : 'Confirm import'}
		</Button>
	</div>
</Modal>
