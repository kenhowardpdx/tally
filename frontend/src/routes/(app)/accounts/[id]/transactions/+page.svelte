<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount, listAccounts } from '$lib/api/accounts';
	import {
		createTransaction,
		deleteTransaction,
		listTransactions,
		updateTransaction
	} from '$lib/api/transactions';
	import type { BankAccount, Transaction } from '$lib/api/types';
	import { accountSuffix } from '$lib/format';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import Select from '$lib/components/Select.svelte';
	import Table from '$lib/components/Table.svelte';
	import { onMount } from 'svelte';

	const accountId = $derived(Number($page.params.id));

	let account = $state<BankAccount | null>(null);
	let accounts = $state<BankAccount[]>([]);
	let transactions = $state<Transaction[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let amount = $state('');
	let date = $state('');
	let description = $state('');
	let creating = $state(false);

	let editingTransaction = $state<Transaction | null>(null);
	let editAmount = $state('');
	let editDate = $state('');
	let editDescription = $state('');
	let saving = $state(false);
	let showEditModal = $state(false);

	let movingTransaction = $state<Transaction | null>(null);
	let moveTargetAccountId = $state('');
	let moving = $state(false);
	let showMoveModal = $state(false);

	// Account details and the accounts list (for the move-transaction picker)
	// only change when navigating here or moving a transaction elsewhere
	// entirely - they don't need refetching after every create/delete,
	// unlike transactions itself.
	async function loadContext() {
		try {
			[account, accounts] = await Promise.all([getAccount(accountId), listAccounts()]);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	async function loadTransactions() {
		loading = true;
		error = null;
		try {
			transactions = await listTransactions(accountId);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadContext();
		loadTransactions();
	});

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
			await loadTransactions();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}

	async function handleDelete(transactionId: number) {
		try {
			await deleteTransaction(accountId, transactionId);
			await loadTransactions();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	function openEditModal(transaction: Transaction) {
		editingTransaction = transaction;
		editAmount = (transaction.amount_cents / 100).toString();
		editDate = transaction.date;
		editDescription = transaction.description ?? '';
		showEditModal = true;
	}

	async function handleEditSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!editingTransaction) return;
		const amountCents = Math.round(Number(editAmount) * 100);
		if (!editDate || Number.isNaN(amountCents)) {
			error = !editDate ? 'Please choose a date.' : 'Please enter a valid amount.';
			return;
		}
		saving = true;
		try {
			await updateTransaction(accountId, editingTransaction.id, {
				amount_cents: amountCents,
				date: editDate,
				description: editDescription || null
			});
			showEditModal = false;
			await loadTransactions();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			saving = false;
		}
	}

	function openMoveModal(transaction: Transaction) {
		movingTransaction = transaction;
		moveTargetAccountId = '';
		showMoveModal = true;
	}

	async function handleMove(event: SubmitEvent) {
		event.preventDefault();
		if (!movingTransaction || !moveTargetAccountId) return;
		moving = true;
		try {
			await updateTransaction(accountId, movingTransaction.id, {
				account_id: Number(moveTargetAccountId)
			});
			showMoveModal = false;
			await loadTransactions();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			moving = false;
		}
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}
</script>

<AccountNav {accountId} current="transactions" />
<h1 class="mt-2 text-2xl font-semibold text-text">
	Transactions{accountSuffix(account)}
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
							<RowActionsMenu
								label="Transaction actions"
								actions={[
									{ label: 'Edit', onclick: () => openEditModal(transaction) },
									{ label: 'Move', onclick: () => openMoveModal(transaction) },
									{
										label: 'Delete',
										onclick: () => handleDelete(transaction.id),
										variant: 'danger'
									}
								]}
							/>
						</td>
					</tr>
				{/each}
			</tbody>
		</Table>
	{/if}
</div>

<Modal bind:open={showMoveModal} title="Move transaction">
	{#if movingTransaction}
		<form class="flex flex-col gap-4" onsubmit={handleMove}>
			<p class="text-sm text-slate-600">
				Move this transaction to a different account.
			</p>
			<Select
				label="Account"
				bind:value={moveTargetAccountId}
				options={accounts
					.filter((a) => a.id !== accountId)
					.map((target) => ({ value: String(target.id), label: target.name }))}
			/>
			<div class="flex justify-end gap-2">
				<Button variant="secondary" type="button" onclick={() => (showMoveModal = false)}>
					Cancel
				</Button>
				<Button type="submit" disabled={moving || !moveTargetAccountId}>Move</Button>
			</div>
		</form>
	{/if}
</Modal>

<Modal bind:open={showEditModal} title="Edit transaction">
	{#if editingTransaction}
		<form class="flex flex-col gap-4" onsubmit={handleEditSubmit}>
			<Input label="Amount ($)" type="number" step="0.01" bind:value={editAmount} required />
			<DatePicker label="Date" bind:value={editDate} />
			<Input label="Description" bind:value={editDescription} placeholder="Optional" />
			<div class="flex justify-end gap-2">
				<Button variant="secondary" type="button" onclick={() => (showEditModal = false)}>
					Cancel
				</Button>
				<Button type="submit" disabled={saving}>Save</Button>
			</div>
		</form>
	{/if}
</Modal>
