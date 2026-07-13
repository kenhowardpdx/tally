<script lang="ts">
	import { page } from '$app/stores';
	import { getBillEventCycleCounts, getBillEvents, getBillHistory, listBills } from '$lib/api/bills';
	import type { Bill, BillEvent, BillHistoryEntry } from '$lib/api/types';
	import { describeBillEvent } from '$lib/billEvents';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import Table from '$lib/components/Table.svelte';
	import { recurrenceLabels } from '$lib/recurrence';
	import { onMount } from 'svelte';

	const accountId = $derived(Number($page.params.id));
	const billId = $derived(Number($page.params.billId));

	const PAGE_SIZE = 20;

	let tab = $state<'cycles' | 'activity'>('cycles');

	let bill = $state<Bill | null>(null);
	let entries = $state<BillHistoryEntry[]>([]);
	let total = $state(0);
	let loading = $state(true);
	let loadingMore = $state(false);

	let events = $state<BillEvent[]>([]);
	let eventsTotal = $state(0);
	let eventsLoadingMore = $state(false);

	// How many activity events exist per cycle_start_date, across the bill's
	// whole history (not just the currently-loaded page of cycle entries) -
	// fetched once up front so every row's "N changes" affordance is free.
	let cycleCounts = $state<Record<string, number>>({});
	// Keyed by the same row key the #each below uses (due_date + cycle_start_date),
	// since a bill that recurs more than once within a single cycle produces
	// multiple rows sharing one cycle_start_date - each expands independently.
	let expandedRows = $state<Record<string, boolean>>({});
	// Keyed by cycle_start_date and shared across same-cycle rows, so
	// expanding a second row for an already-fetched cycle doesn't refetch.
	let cycleEvents = $state<Record<string, BillEvent[]>>({});
	let cycleEventsLoading = $state<Record<string, boolean>>({});

	let error = $state<string | null>(null);

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	function formatTimestamp(iso: string): string {
		return new Date(iso).toLocaleString(undefined, {
			dateStyle: 'medium',
			timeStyle: 'short'
		});
	}

	async function load() {
		loading = true;
		error = null;
		try {
			const [bills, history, eventList, cycleCountsResponse] = await Promise.all([
				listBills(accountId),
				getBillHistory(accountId, billId, { limit: PAGE_SIZE, offset: 0 }),
				getBillEvents(accountId, billId, { limit: PAGE_SIZE, offset: 0 }),
				getBillEventCycleCounts(accountId, billId)
			]);
			bill = bills.find((b) => b.id === billId) ?? null;
			entries = history.entries;
			total = history.total;
			events = eventList.events;
			eventsTotal = eventList.total;
			cycleCounts = Object.fromEntries(
				cycleCountsResponse.counts.map((c) => [c.cycle_start_date, c.count])
			);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	}

	async function toggleRowExpansion(entry: BillHistoryEntry) {
		const rowKey = entry.due_date + entry.cycle_start_date;
		const nowExpanded = !expandedRows[rowKey];
		expandedRows = { ...expandedRows, [rowKey]: nowExpanded };
		if (!nowExpanded || cycleEvents[entry.cycle_start_date]) return;

		cycleEventsLoading = { ...cycleEventsLoading, [entry.cycle_start_date]: true };
		try {
			const res = await getBillEvents(accountId, billId, {
				cycle_start_date: entry.cycle_start_date,
				limit: 200
			});
			cycleEvents = { ...cycleEvents, [entry.cycle_start_date]: res.events };
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			cycleEventsLoading = { ...cycleEventsLoading, [entry.cycle_start_date]: false };
		}
	}

	async function loadMore() {
		loadingMore = true;
		error = null;
		try {
			const history = await getBillHistory(accountId, billId, {
				limit: PAGE_SIZE,
				offset: entries.length
			});
			entries = [...entries, ...history.entries];
			total = history.total;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loadingMore = false;
		}
	}

	async function loadMoreEvents() {
		eventsLoadingMore = true;
		error = null;
		try {
			const eventList = await getBillEvents(accountId, billId, {
				limit: PAGE_SIZE,
				offset: events.length
			});
			events = [...events, ...eventList.events];
			eventsTotal = eventList.total;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			eventsLoadingMore = false;
		}
	}

	onMount(load);
</script>

<a class="text-sm text-primary underline" href="/accounts/{accountId}">&larr; Bills</a>
<h1 class="mt-2 text-2xl font-semibold text-text">
	{bill ? `History - ${bill.name}` : 'History'}
</h1>
{#if bill}
	<p class="mt-1 text-sm text-slate-500">
		{formatAmount(bill.amount_cents)} - {recurrenceLabels[bill.recurrence_type]}
	</p>
{/if}

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<div class="mt-6 flex gap-2 border-b border-slate-200">
	<button
		class="border-b-2 px-3 py-2 text-sm font-medium {tab === 'cycles'
			? 'border-primary text-primary'
			: 'border-transparent text-slate-500 hover:text-slate-700'}"
		onclick={() => (tab = 'cycles')}
	>
		Cycle history
	</button>
	<button
		class="border-b-2 px-3 py-2 text-sm font-medium {tab === 'activity'
			? 'border-primary text-primary'
			: 'border-transparent text-slate-500 hover:text-slate-700'}"
		onclick={() => (tab = 'activity')}
	>
		Activity{eventsTotal ? ` (${eventsTotal})` : ''}
	</button>
</div>

<div class="mt-4">
	{#if loading}
		<p class="text-sm text-slate-500">Loading...</p>
	{:else if tab === 'cycles'}
		{#if entries.length === 0}
			<p class="text-sm text-slate-500">No cycle history yet for this bill.</p>
		{:else}
			<Card>
				<Table>
					<thead>
						<tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
							<th class="px-4 py-2 font-medium">Due date</th>
							<th class="px-4 py-2 font-medium">Cycle</th>
							<th class="px-4 py-2 text-right font-medium">Expected</th>
							<th class="px-4 py-2 text-right font-medium">Actual</th>
							<th class="px-4 py-2 text-right font-medium">Variance</th>
							<th class="px-4 py-2 font-medium">Paid</th>
							<th class="px-4 py-2 font-medium">Notes</th>
							<th class="px-4 py-2 font-medium">Activity</th>
						</tr>
					</thead>
					<tbody>
						{#each entries as entry (entry.due_date + entry.cycle_start_date)}
							{@const rowKey = entry.due_date + entry.cycle_start_date}
							{@const count = cycleCounts[entry.cycle_start_date] ?? 0}
							<tr class="border-b border-slate-100 text-sm last:border-0">
								<td class="px-4 py-2">{entry.due_date}</td>
								<td class="px-4 py-2 text-slate-500">
									{entry.cycle_start_date} - {entry.cycle_end_date}
								</td>
								<td class="px-4 py-2 text-right">{formatAmount(entry.expected_amount_cents)}</td>
								<td class="px-4 py-2 text-right">{formatAmount(entry.actual_amount_cents)}</td>
								<td
									class="px-4 py-2 text-right {entry.variance_cents === 0
										? 'text-slate-500'
										: entry.variance_cents > 0
											? 'text-red-700'
											: 'text-emerald-700'}"
								>
									{formatAmount(entry.variance_cents)}
								</td>
								<td class="px-4 py-2">
									{#if entry.completed}
										<span
											class="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
										>
											Paid
										</span>
									{:else}
										<span class="text-xs text-slate-400">-</span>
									{/if}
								</td>
								<td class="px-4 py-2 text-slate-600">{entry.notes ?? ''}</td>
								<td class="px-4 py-2">
									{#if count > 0}
										<button
											class="text-xs text-primary underline"
											onclick={() => toggleRowExpansion(entry)}
										>
											{count} change{count === 1 ? '' : 's'}
											{expandedRows[rowKey] ? '▴' : '▾'}
										</button>
									{:else}
										<span class="text-xs text-slate-400">-</span>
									{/if}
								</td>
							</tr>
							{#if expandedRows[rowKey]}
								<tr class="border-b border-slate-100 bg-slate-50 text-xs">
									<td class="px-4 py-3" colspan="8">
										{#if cycleEventsLoading[entry.cycle_start_date]}
											<p class="text-slate-500">Loading…</p>
										{:else}
											<ul class="space-y-2">
												{#each cycleEvents[entry.cycle_start_date] ?? [] as event (event.id)}
													{@const described = describeBillEvent(event, formatAmount)}
													<li>
														<div class="flex flex-wrap items-baseline justify-between gap-x-4">
															<span class="font-medium text-text">{described.label}</span>
															<span class="text-slate-500">{formatTimestamp(event.created_at)}</span>
														</div>
														{#if described.details.length}
															<ul class="mt-0.5 space-y-0.5 text-slate-600">
																{#each described.details as detail (detail)}
																	<li>{detail}</li>
																{/each}
															</ul>
														{/if}
													</li>
												{/each}
											</ul>
										{/if}
									</td>
								</tr>
							{/if}
						{/each}
					</tbody>
				</Table>
			</Card>
			{#if entries.length < total}
				<div class="mt-4 flex justify-center">
					<Button variant="secondary" onclick={loadMore} disabled={loadingMore}>
						{loadingMore ? 'Loading…' : `Load more (${entries.length} of ${total})`}
					</Button>
				</div>
			{/if}
		{/if}
	{:else if events.length === 0}
		<p class="text-sm text-slate-500">No activity recorded yet for this bill.</p>
	{:else}
		<Card>
			<ul class="divide-y divide-slate-100">
				{#each events as event (event.id)}
					{@const described = describeBillEvent(event, formatAmount)}
					<li class="px-4 py-3 text-sm">
						<div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
							<span class="font-medium text-text">{described.label}</span>
							<span class="text-xs text-slate-500">{formatTimestamp(event.created_at)}</span>
						</div>
						{#if event.cycle_start_date}
							<p class="mt-0.5 text-xs text-slate-500">Cycle starting {event.cycle_start_date}</p>
						{/if}
						{#if described.details.length}
							<ul class="mt-1 space-y-0.5 text-xs text-slate-600">
								{#each described.details as detail (detail)}
									<li>{detail}</li>
								{/each}
							</ul>
						{/if}
					</li>
				{/each}
			</ul>
		</Card>
		{#if events.length < eventsTotal}
			<div class="mt-4 flex justify-center">
				<Button variant="secondary" onclick={loadMoreEvents} disabled={eventsLoadingMore}>
					{eventsLoadingMore ? 'Loading…' : `Load more (${events.length} of ${eventsTotal})`}
				</Button>
			</div>
		{/if}
	{/if}
</div>
