<script lang="ts">
	import { page } from '$app/stores';
	import { getBillHistory, listBills } from '$lib/api/bills';
	import type { Bill, BillHistoryEntry } from '$lib/api/types';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import Table from '$lib/components/Table.svelte';
	import { recurrenceLabels } from '$lib/recurrence';
	import { onMount } from 'svelte';

	const accountId = $derived(Number($page.params.id));
	const billId = $derived(Number($page.params.billId));

	const PAGE_SIZE = 20;

	let bill = $state<Bill | null>(null);
	let entries = $state<BillHistoryEntry[]>([]);
	let total = $state(0);
	let loading = $state(true);
	let loadingMore = $state(false);
	let error = $state<string | null>(null);

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	async function load() {
		loading = true;
		error = null;
		try {
			const [bills, history] = await Promise.all([
				listBills(accountId),
				getBillHistory(accountId, billId, { limit: PAGE_SIZE, offset: 0 })
			]);
			bill = bills.find((b) => b.id === billId) ?? null;
			entries = history.entries;
			total = history.total;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
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

<div class="mt-6">
	{#if loading}
		<p class="text-sm text-slate-500">Loading...</p>
	{:else if entries.length === 0}
		<p class="text-sm text-slate-500">No history yet for this bill.</p>
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
					</tr>
				</thead>
				<tbody>
					{#each entries as entry (entry.due_date + entry.cycle_start_date)}
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
						</tr>
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
</div>
