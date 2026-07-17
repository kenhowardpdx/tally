<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount, listAccounts } from '$lib/api/accounts';
	import { createWindfall, deleteWindfall, listWindfalls, updateWindfall } from '$lib/api/windfalls';
	import type { BankAccount, Windfall } from '$lib/api/types';
	import { accountSuffix } from '$lib/format';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import Select from '$lib/components/Select.svelte';
	import Table from '$lib/components/Table.svelte';
	import Tooltip from '$lib/components/Tooltip.svelte';
	import { glossaryTerms } from '$lib/glossary';
	import { onMount } from 'svelte';

	const windfallTooltip = glossaryTerms.find((t) => t.term === 'Windfall')!.definition;

	const accountId = $derived(Number($page.params.id));

	let account = $state<BankAccount | null>(null);
	let accounts = $state<BankAccount[]>([]);
	let windfalls = $state<Windfall[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let name = $state('');
	let amount = $state('');
	let expectedDate = $state('');
	let creating = $state(false);

	let editingWindfall = $state<Windfall | null>(null);
	let editName = $state('');
	let editAmount = $state('');
	let editExpectedDate = $state('');
	let saving = $state(false);
	let showEditModal = $state(false);

	let movingWindfall = $state<Windfall | null>(null);
	let moveTargetAccountId = $state('');
	let moving = $state(false);
	let showMoveModal = $state(false);

	// Account details and the accounts list (for the move-windfall picker)
	// only change when navigating here or moving a windfall elsewhere
	// entirely - they don't need refetching after every create/delete,
	// unlike windfalls itself.
	async function loadContext() {
		try {
			[account, accounts] = await Promise.all([getAccount(accountId), listAccounts()]);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	async function loadWindfalls() {
		loading = true;
		error = null;
		try {
			windfalls = await listWindfalls(accountId);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadContext();
		loadWindfalls();
	});

	async function handleCreate(event: SubmitEvent) {
		event.preventDefault();
		const amountCents = Math.round(Number(amount) * 100);
		if (!name.trim() || !expectedDate || Number.isNaN(amountCents) || amountCents <= 0) {
			error = !expectedDate
				? 'Please choose an expected date.'
				: amountCents <= 0
					? 'Amount must be greater than zero.'
					: 'Please fill out all fields.';
			return;
		}
		creating = true;
		try {
			await createWindfall(accountId, {
				name,
				amount_cents: amountCents,
				expected_date: expectedDate
			});
			name = '';
			amount = '';
			expectedDate = '';
			await loadWindfalls();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}

	async function toggleEnabled(windfall: Windfall) {
		try {
			await updateWindfall(accountId, windfall.id, { enabled: !windfall.enabled });
			await loadWindfalls();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	async function handleDelete(windfallId: number) {
		try {
			await deleteWindfall(accountId, windfallId);
			await loadWindfalls();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	function openEditModal(windfall: Windfall) {
		editingWindfall = windfall;
		editName = windfall.name;
		editAmount = (windfall.amount_cents / 100).toString();
		editExpectedDate = windfall.expected_date;
		showEditModal = true;
	}

	async function handleEditSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!editingWindfall) return;
		const amountCents = Math.round(Number(editAmount) * 100);
		if (!editName.trim() || !editExpectedDate || Number.isNaN(amountCents) || amountCents <= 0) {
			error = !editExpectedDate
				? 'Please choose an expected date.'
				: amountCents <= 0
					? 'Amount must be greater than zero.'
					: 'Please fill out all fields.';
			return;
		}
		saving = true;
		try {
			await updateWindfall(accountId, editingWindfall.id, {
				name: editName,
				amount_cents: amountCents,
				expected_date: editExpectedDate
			});
			showEditModal = false;
			await loadWindfalls();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			saving = false;
		}
	}

	function openMoveModal(windfall: Windfall) {
		movingWindfall = windfall;
		moveTargetAccountId = '';
		showMoveModal = true;
	}

	async function handleMove(event: SubmitEvent) {
		event.preventDefault();
		if (!movingWindfall || !moveTargetAccountId) return;
		moving = true;
		try {
			await updateWindfall(accountId, movingWindfall.id, {
				account_id: Number(moveTargetAccountId)
			});
			showMoveModal = false;
			await loadWindfalls();
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

<AccountNav {accountId} current="windfalls" />
<h1 class="mt-2 flex items-center text-2xl font-semibold text-text">
	Windfalls{accountSuffix(account)}
	<Tooltip text={windfallTooltip} />
</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCreate}>
		<Input label="Name" bind:value={name} placeholder="Tax refund" required />
		<Input
			label="Amount ($)"
			type="number"
			step="0.01"
			bind:value={amount}
			placeholder="500.00"
			required
		/>
		<DatePicker label="Expected date" bind:value={expectedDate} />
		<Button type="submit" disabled={creating}>Add windfall</Button>
	</form>
</Card>

<div class="mt-6">
	{#if loading}
		<p class="text-sm text-slate-500">Loading...</p>
	{:else if windfalls.length === 0}
		<p class="text-sm text-slate-500">No windfalls yet.</p>
	{:else}
		<Table>
			<thead>
				<tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
					<th class="px-4 py-2 font-medium">Expected date</th>
					<th class="px-4 py-2 font-medium">Name</th>
					<th class="px-4 py-2 text-right font-medium">Amount</th>
					<th class="px-4 py-2"></th>
					<th class="px-4 py-2"></th>
				</tr>
			</thead>
			<tbody>
				{#each windfalls as windfall (windfall.id)}
					<tr class="border-b border-slate-100 last:border-0">
						<td class="px-4 py-2">{windfall.expected_date}</td>
						<td class="px-4 py-2">{windfall.name}</td>
						<td class="px-4 py-2 text-right text-emerald-700">
							{formatAmount(windfall.amount_cents)}
						</td>
						<td class="px-4 py-2">
							<button onclick={() => toggleEnabled(windfall)}>
								<Badge enabled={windfall.enabled} />
							</button>
						</td>
						<td class="px-4 py-2 text-right">
							<RowActionsMenu
								label="Windfall actions"
								actions={[
									{ label: 'Edit', onclick: () => openEditModal(windfall) },
									{ label: 'Move', onclick: () => openMoveModal(windfall) },
									{ label: 'Delete', onclick: () => handleDelete(windfall.id), variant: 'danger' }
								]}
							/>
						</td>
					</tr>
				{/each}
			</tbody>
		</Table>
	{/if}
</div>

<Modal bind:open={showMoveModal} title="Move windfall">
	{#if movingWindfall}
		<form class="flex flex-col gap-4" onsubmit={handleMove}>
			<p class="text-sm text-slate-600">
				Move <span class="font-medium text-text">{movingWindfall.name}</span> to a different account.
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

<Modal bind:open={showEditModal} title="Edit windfall">
	{#if editingWindfall}
		<form class="flex flex-col gap-4" onsubmit={handleEditSubmit}>
			<Input label="Name" bind:value={editName} required />
			<Input label="Amount ($)" type="number" step="0.01" bind:value={editAmount} required />
			<DatePicker label="Expected date" bind:value={editExpectedDate} />
			<div class="flex justify-end gap-2">
				<Button variant="secondary" type="button" onclick={() => (showEditModal = false)}>
					Cancel
				</Button>
				<Button type="submit" disabled={saving}>Save</Button>
			</div>
		</form>
	{/if}
</Modal>
