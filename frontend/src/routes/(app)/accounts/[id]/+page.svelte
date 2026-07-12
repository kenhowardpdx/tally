<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount, listAccounts } from '$lib/api/accounts';
	import { createBill, deleteBill, listBills, updateBill } from '$lib/api/bills';
	import type { BankAccount, Bill, RecurrenceType } from '$lib/api/types';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import Select from '$lib/components/Select.svelte';
	import Table from '$lib/components/Table.svelte';
	import { recurrenceLabels } from '$lib/recurrence';
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

	let account = $state<BankAccount | null>(null);
	let accounts = $state<BankAccount[]>([]);
	let bills = $state<Bill[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let name = $state('');
	let amount = $state('');
	let recurrenceType = $state<RecurrenceType>('monthly');
	let startDate = $state('');
	let creating = $state(false);

	let movingBill = $state<Bill | null>(null);
	let moveTargetAccountId = $state('');
	let moving = $state(false);
	let showMoveModal = $state(false);

	// Account details and the accounts list (for the move-bill picker) only
	// change when navigating here or moving a bill elsewhere entirely - they
	// don't need refetching after every bill create/toggle/delete, unlike
	// bills itself.
	async function loadContext() {
		try {
			[account, accounts] = await Promise.all([getAccount(accountId), listAccounts()]);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	async function loadBills() {
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

	onMount(() => {
		loadContext();
		loadBills();
	});

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
			await loadBills();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}

	async function toggleEnabled(bill: Bill) {
		try {
			await updateBill(accountId, bill.id, { enabled: !bill.enabled });
			await loadBills();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	async function handleDelete(billId: number) {
		try {
			await deleteBill(accountId, billId);
			await loadBills();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	function openMoveModal(bill: Bill) {
		movingBill = bill;
		moveTargetAccountId = '';
		showMoveModal = true;
	}

	async function handleMove(event: SubmitEvent) {
		event.preventDefault();
		if (!movingBill || !moveTargetAccountId) return;
		moving = true;
		try {
			await updateBill(accountId, movingBill.id, { account_id: Number(moveTargetAccountId) });
			showMoveModal = false;
			await loadBills();
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

<AccountNav {accountId} current="bills" />
<h1 class="mt-2 text-2xl font-semibold text-text">
	Bills{#if account} ({account.name}{#if account.institution} - {account.institution}{/if}){/if}
</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCreate}>
		<Input label="Name" bind:value={name} placeholder="Rent" required />
		<Input label="Amount ($)" type="number" bind:value={amount} placeholder="1500.00" required />
		<Select label="Frequency" bind:value={recurrenceType}>
			{#each recurrenceOptions as option (option)}
				<option value={option}>{recurrenceLabels[option]}</option>
			{/each}
		</Select>
		<DatePicker label="Start date" bind:value={startDate} />
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
					<th class="px-4 py-2 font-medium">Frequency</th>
					<th class="px-4 py-2 font-medium">Status</th>
					<th class="px-4 py-2"></th>
				</tr>
			</thead>
			<tbody>
				{#each bills as bill (bill.id)}
					<tr class="border-b border-slate-100 last:border-0">
						<td class="px-4 py-2">{bill.name}</td>
						<td class="px-4 py-2">{formatAmount(bill.amount_cents)}</td>
						<td class="px-4 py-2 text-slate-600">{recurrenceLabels[bill.recurrence_type]}</td>
						<td class="px-4 py-2">
							<button onclick={() => toggleEnabled(bill)}>
								<Badge enabled={bill.enabled} />
							</button>
						</td>
						<td class="px-4 py-2 text-right">
							<div class="flex justify-end gap-2">
								<Button variant="secondary" onclick={() => openMoveModal(bill)}>Move</Button>
								<Button variant="danger" onclick={() => handleDelete(bill.id)}>Delete</Button>
							</div>
						</td>
					</tr>
				{/each}
			</tbody>
		</Table>
	{/if}
</div>

<Modal bind:open={showMoveModal} title="Move bill">
	{#if movingBill}
		<form class="flex flex-col gap-4" onsubmit={handleMove}>
			<p class="text-sm text-slate-600">
				Move <span class="font-medium text-text">{movingBill.name}</span> to a different account.
			</p>
			<Select label="Account" bind:value={moveTargetAccountId} required>
				<option value="" disabled>Select an account</option>
				{#each accounts.filter((a) => a.id !== accountId) as target (target.id)}
					<option value={target.id}>{target.name}</option>
				{/each}
			</Select>
			<div class="flex justify-end gap-2">
				<Button variant="secondary" type="button" onclick={() => (showMoveModal = false)}>
					Cancel
				</Button>
				<Button type="submit" disabled={moving || !moveTargetAccountId}>Move</Button>
			</div>
		</form>
	{/if}
</Modal>
