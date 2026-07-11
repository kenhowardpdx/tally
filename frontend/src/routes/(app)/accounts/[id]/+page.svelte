<script lang="ts">
	import { page } from '$app/stores';
	import { createBill, deleteBill, listBills, updateBill } from '$lib/api/bills';
	import type { Bill, RecurrenceType } from '$lib/api/types';
	import Badge from '$lib/components/Badge.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import Input from '$lib/components/Input.svelte';
	import Table from '$lib/components/Table.svelte';
	import { onMount } from 'svelte';

	const accountId = $derived(Number($page.params.id));

	const recurrenceOptions: RecurrenceType[] = [
		'weekly',
		'biweekly',
		'semimonthly',
		'monthly',
		'annually',
		'custom_days'
	];

	let bills = $state<Bill[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let name = $state('');
	let amount = $state('');
	let recurrenceType = $state<RecurrenceType>('monthly');
	let startDate = $state('');
	let creating = $state(false);

	async function load() {
		loading = true;
		error = null;
		try {
			bills = await listBills(accountId);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	}

	onMount(load);

	async function handleCreate(event: SubmitEvent) {
		event.preventDefault();
		const amountCents = Math.round(Number(amount) * 100);
		if (!name.trim() || !startDate || Number.isNaN(amountCents)) return;
		creating = true;
		try {
			await createBill(accountId, {
				name,
				amount_cents: amountCents,
				recurrence_type: recurrenceType,
				start_date: startDate
			});
			name = '';
			amount = '';
			startDate = '';
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}

	async function toggleEnabled(bill: Bill) {
		try {
			await updateBill(accountId, bill.id, { enabled: !bill.enabled });
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	async function handleDelete(billId: number) {
		try {
			await deleteBill(accountId, billId);
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}
</script>

<a class="text-sm text-primary underline" href="/accounts">&larr; Accounts</a>
<h1 class="mt-2 text-2xl font-semibold text-text">Bills</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCreate}>
		<Input label="Name" bind:value={name} placeholder="Rent" required />
		<Input label="Amount ($)" type="number" bind:value={amount} placeholder="1500.00" required />
		<div class="flex flex-col gap-1">
			<label for="recurrence" class="text-sm font-medium text-text">Recurrence</label>
			<select
				id="recurrence"
				bind:value={recurrenceType}
				class="rounded-card border border-slate-300 px-3 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
			>
				{#each recurrenceOptions as option (option)}
					<option value={option}>{option}</option>
				{/each}
			</select>
		</div>
		<Input label="Start date" type="date" bind:value={startDate} required />
		<Button type="submit" disabled={creating}>Add bill</Button>
	</form>
</Card>

<div class="mt-6">
	{#if loading}
		<p class="text-sm text-slate-500">Loading...</p>
	{:else if bills.length === 0}
		<p class="text-sm text-slate-500">No bills yet.</p>
	{:else}
		<Table>
			<thead>
				<tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
					<th class="px-4 py-2 font-medium">Name</th>
					<th class="px-4 py-2 font-medium">Amount</th>
					<th class="px-4 py-2 font-medium">Recurrence</th>
					<th class="px-4 py-2 font-medium">Status</th>
					<th class="px-4 py-2"></th>
				</tr>
			</thead>
			<tbody>
				{#each bills as bill (bill.id)}
					<tr class="border-b border-slate-100 last:border-0">
						<td class="px-4 py-2">{bill.name}</td>
						<td class="px-4 py-2">{formatAmount(bill.amount_cents)}</td>
						<td class="px-4 py-2 text-slate-600">{bill.recurrence_type}</td>
						<td class="px-4 py-2">
							<button onclick={() => toggleEnabled(bill)}>
								<Badge enabled={bill.enabled} />
							</button>
						</td>
						<td class="px-4 py-2 text-right">
							<Button variant="danger" onclick={() => handleDelete(bill.id)}>Delete</Button>
						</td>
					</tr>
				{/each}
			</tbody>
		</Table>
	{/if}
</div>
