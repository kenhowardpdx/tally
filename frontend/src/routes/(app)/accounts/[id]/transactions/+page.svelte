<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount } from '$lib/api/accounts';
	import { createTransaction, deleteTransaction, listTransactions } from '$lib/api/transactions';
	import type { BankAccount, Transaction } from '$lib/api/types';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Table from '$lib/components/Table.svelte';
	import { onMount } from 'svelte';

	const accountId = $derived(Number($page.params.id));

	let account = $state<BankAccount | null>(null);
	let transactions = $state<Transaction[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let amount = $state('');
	let date = $state('');
	let description = $state('');
	let creating = $state(false);

	async function load() {
		loading = true;
		error = null;
		try {
			[account, transactions] = await Promise.all([
				getAccount(accountId),
				listTransactions(accountId)
			]);
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
		if (!date || Number.isNaN(amountCents)) {
			error = !date ? 'Please choose a date.' : 'Please enter a valid amount.';
			return;
		}
		creating = true;
		try {
			await createTransaction(accountId, {
				amount_cents: amountCents,
				date,
				description: description || null
			});
			amount = '';
			date = '';
			description = '';
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}

	async function handleDelete(transactionId: number) {
		try {
			await deleteTransaction(accountId, transactionId);
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}
</script>

<AccountNav {accountId} current="transactions" />
<h1 class="mt-2 text-2xl font-semibold text-text">
	Transactions{#if account} ({account.name}{#if account.institution} - {account.institution}{/if}){/if}
</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCreate}>
		<Input
			label="Amount ($)"
			type="number"
			step="0.01"
			bind:value={amount}
			placeholder="-25.00"
			required
		/>
		<DatePicker label="Date" bind:value={date} />
		<Input label="Description" bind:value={description} placeholder="Optional" />
		<Button type="submit" disabled={creating}>Add transaction</Button>
	</form>
</Card>

<div class="mt-6">
	{#if loading}
		<p class="text-sm text-slate-500">Loading...</p>
	{:else if transactions.length === 0}
		<p class="text-sm text-slate-500">No transactions yet.</p>
	{:else}
		<Table>
			<thead>
				<tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
					<th class="px-4 py-2 font-medium">Date</th>
					<th class="px-4 py-2 font-medium">Description</th>
					<th class="px-4 py-2 text-right font-medium">Amount</th>
					<th class="px-4 py-2"></th>
				</tr>
			</thead>
			<tbody>
				{#each transactions as transaction (transaction.id)}
					<tr class="border-b border-slate-100 last:border-0">
						<td class="px-4 py-2">{transaction.date}</td>
						<td class="px-4 py-2 text-slate-600">{transaction.description ?? '—'}</td>
						<td
							class="px-4 py-2 text-right {transaction.amount_cents < 0
								? 'text-red-700'
								: 'text-emerald-700'}"
						>
							{formatAmount(transaction.amount_cents)}
						</td>
						<td class="px-4 py-2 text-right">
							<Button variant="danger" onclick={() => handleDelete(transaction.id)}>Delete</Button>
						</td>
					</tr>
				{/each}
			</tbody>
		</Table>
	{/if}
</div>
