<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount } from '$lib/api/accounts';
	import { createWindfall, deleteWindfall, listWindfalls } from '$lib/api/windfalls';
	import type { BankAccount, Windfall } from '$lib/api/types';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Table from '$lib/components/Table.svelte';
	import Tooltip from '$lib/components/Tooltip.svelte';
	import { glossaryTerms } from '$lib/glossary';
	import { onMount } from 'svelte';

	const windfallTooltip = glossaryTerms.find((t) => t.term === 'Windfall')!.definition;

	const accountId = $derived(Number($page.params.id));

	let account = $state<BankAccount | null>(null);
	let windfalls = $state<Windfall[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let name = $state('');
	let amount = $state('');
	let expectedDate = $state('');
	let creating = $state(false);

	async function load() {
		loading = true;
		error = null;
		try {
			[account, windfalls] = await Promise.all([
				getAccount(accountId),
				listWindfalls(accountId)
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
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}

	async function handleDelete(windfallId: number) {
		try {
			await deleteWindfall(accountId, windfallId);
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}
</script>

<AccountNav {accountId} current="windfalls" />
<h1 class="mt-2 flex items-center text-2xl font-semibold text-text">
	Windfalls{#if account}
		({account.name}{#if account.institution} - {account.institution}{/if}){/if}
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
						<td class="px-4 py-2 text-right">
							<Button variant="danger" onclick={() => handleDelete(windfall.id)}>Delete</Button>
						</td>
					</tr>
				{/each}
			</tbody>
		</Table>
	{/if}
</div>
