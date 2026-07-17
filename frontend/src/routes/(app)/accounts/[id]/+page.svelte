<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount, listAccounts } from '$lib/api/accounts';
	import { createBill, deleteBill, listBills, updateBill } from '$lib/api/bills';
	import type { BankAccount, Bill, RecurrenceType } from '$lib/api/types';
	import { accountSuffix, todayIso } from '$lib/format';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import RecurrenceConfigFields from '$lib/components/RecurrenceConfigFields.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import Select from '$lib/components/Select.svelte';
	import Table from '$lib/components/Table.svelte';
	import Tooltip from '$lib/components/Tooltip.svelte';
	import { glossaryTerms } from '$lib/glossary';
	import { recurrenceLabels } from '$lib/recurrence';
	import { onMount } from 'svelte';

	const frequencyTooltip = glossaryTerms.find((t) => t.term === 'Frequency')!.definition;
	const oneTimeTooltip = glossaryTerms.find((t) => t.term === 'One-time bill')!.definition;
	const endedTooltip = glossaryTerms.find((t) => t.term === 'Ended bill')!.definition;
	const today = todayIso();

	function isOneTimeBill(bill: Bill): boolean {
		return bill.end_date !== null && bill.start_date === bill.end_date;
	}

	function isEndedBill(bill: Bill): boolean {
		return bill.end_date !== null && bill.end_date < today;
	}

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
	let recurrenceConfig = $state<Record<string, unknown>>({});
	let startDate = $state('');
	let notes = $state('');
	let creating = $state(false);
	let recurrenceFieldsResetKey = $state(0);

	let movingBill = $state<Bill | null>(null);
	let moveTargetAccountId = $state('');
	let moving = $state(false);
	let showMoveModal = $state(false);

	let editingBill = $state<Bill | null>(null);
	let editName = $state('');
	let editAmount = $state('');
	let editRecurrenceType = $state<RecurrenceType>('monthly');
	let editRecurrenceConfig = $state<Record<string, unknown>>({});
	let editStartDate = $state('');
	let editEndDate = $state('');
	let editEnabled = $state(true);
	let editNotes = $state('');
	let saving = $state(false);
	let showEditModal = $state(false);

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
		if (!name.trim() || !startDate || Number.isNaN(amountCents)) {
			error = 'Please fill out all required fields.';
			return;
		}
		creating = true;
		try {
			await createBill(accountId, {
				name,
				amount_cents: amountCents,
				recurrence_type: recurrenceType,
				recurrence_config: recurrenceConfig,
				start_date: startDate,
				notes: notes || null
			});
			name = '';
			amount = '';
			recurrenceConfig = {};
			// RecurrenceConfigFields only seeds its local day/interval inputs
			// from recurrenceConfig once at mount - remounting it (via the
			// {#key} block below) is what makes the reset above actually
			// clear what's displayed, not just the value bound to the parent.
			recurrenceFieldsResetKey += 1;
			startDate = '';
			notes = '';
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

	function openEditModal(bill: Bill) {
		editingBill = bill;
		editName = bill.name;
		editAmount = (bill.amount_cents / 100).toString();
		editRecurrenceType = bill.recurrence_type;
		editRecurrenceConfig = { ...bill.recurrence_config };
		editStartDate = bill.start_date;
		editEndDate = bill.end_date ?? '';
		editEnabled = bill.enabled;
		editNotes = bill.notes ?? '';
		showEditModal = true;
	}

	async function handleEditSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!editingBill) return;
		const amountCents = Math.round(Number(editAmount) * 100);
		if (!editName.trim() || !editStartDate || Number.isNaN(amountCents)) {
			error = 'Please fill out all required fields.';
			return;
		}
		saving = true;
		try {
			await updateBill(accountId, editingBill.id, {
				name: editName,
				amount_cents: amountCents,
				recurrence_type: editRecurrenceType,
				recurrence_config: editRecurrenceConfig,
				start_date: editStartDate,
				end_date: editEndDate || null,
				enabled: editEnabled,
				notes: editNotes || null
			});
			showEditModal = false;
			await loadBills();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			saving = false;
		}
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}
</script>

<AccountNav {accountId} current="bills" />
<h1 class="mt-2 text-2xl font-semibold text-text">
	Bills{accountSuffix(account)}
</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCreate}>
		<Input label="Name" bind:value={name} placeholder="Rent" required />
		<Input
			label="Amount ($)"
			type="number"
			step="0.01"
			bind:value={amount}
			placeholder="1500.00"
			required
		/>
		<Select
			label="Frequency"
			bind:value={recurrenceType}
			options={recurrenceOptions.map((option) => ({ value: option, label: recurrenceLabels[option] }))}
			tooltip={frequencyTooltip}
		/>
		{#key recurrenceFieldsResetKey}
			<RecurrenceConfigFields {recurrenceType} bind:recurrenceConfig />
		{/key}
		<DatePicker label="Start date" bind:value={startDate} />
		<Input label="Notes" bind:value={notes} placeholder="Optional" />
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
						<td class="px-4 py-2">
							<div class="flex flex-wrap items-center gap-1.5">
								<span>{bill.name}</span>
								{#if isOneTimeBill(bill)}
									<span
										class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
									>
										One-time
										<Tooltip text={oneTimeTooltip} />
									</span>
								{/if}
								{#if isEndedBill(bill)}
									<span
										class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
									>
										Ended
										<Tooltip text={endedTooltip} />
									</span>
								{/if}
							</div>
						</td>
						<td class="px-4 py-2">{formatAmount(bill.amount_cents)}</td>
						<td class="px-4 py-2 text-slate-600">{recurrenceLabels[bill.recurrence_type]}</td>
						<td class="px-4 py-2">
							<button onclick={() => toggleEnabled(bill)}>
								<Badge enabled={bill.enabled} />
							</button>
						</td>
						<td class="px-4 py-2 text-right">
							<div class="flex items-center justify-end gap-2">
								<a
									class="text-sm text-primary underline"
									href="/accounts/{accountId}/bills/{bill.id}/history"
								>
									History
								</a>
								<RowActionsMenu
									label="Bill actions"
									actions={[
										{ label: 'Edit', onclick: () => openEditModal(bill) },
										{ label: 'Move', onclick: () => openMoveModal(bill) },
										{ label: 'Delete', onclick: () => handleDelete(bill.id), variant: 'danger' }
									]}
								/>
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

<Modal bind:open={showEditModal} title="Edit bill">
	{#if editingBill}
		<form class="flex flex-col gap-4" onsubmit={handleEditSubmit}>
			<Input label="Name" bind:value={editName} required />
			<Input label="Amount ($)" type="number" step="0.01" bind:value={editAmount} required />
			<Select
				label="Frequency"
				bind:value={editRecurrenceType}
				options={recurrenceOptions.map((option) => ({ value: option, label: recurrenceLabels[option] }))}
				tooltip={frequencyTooltip}
			/>
			<RecurrenceConfigFields
				recurrenceType={editRecurrenceType}
				bind:recurrenceConfig={editRecurrenceConfig}
			/>
			<DatePicker label="Start date" bind:value={editStartDate} />
			<div class="flex items-end gap-2">
				<DatePicker label="End date (optional)" bind:value={editEndDate} />
				{#if editEndDate}
					<Button variant="secondary" type="button" onclick={() => (editEndDate = '')}>
						Clear
					</Button>
				{/if}
			</div>
			<Input label="Notes" bind:value={editNotes} placeholder="Optional" />
			<label class="flex items-center gap-2 text-sm text-text">
				<input type="checkbox" bind:checked={editEnabled} />
				Enabled
			</label>
			<div class="flex justify-end gap-2">
				<Button variant="secondary" type="button" onclick={() => (showEditModal = false)}>
					Cancel
				</Button>
				<Button type="submit" disabled={saving}>Save</Button>
			</div>
		</form>
	{/if}
</Modal>
