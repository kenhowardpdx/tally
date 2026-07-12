<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount } from '$lib/api/accounts';
	import { computeForecast } from '$lib/api/forecast';
	import type { BankAccount, CycleType, ForecastResponse } from '$lib/api/types';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Select from '$lib/components/Select.svelte';
	import Table from '$lib/components/Table.svelte';
	import { cycleTypeLabels } from '$lib/cycle';
	import { onMount } from 'svelte';

	const accountId = $derived(Number($page.params.id));

	const cycleTypeOptions: CycleType[] = ['weekly', 'biweekly', 'monthly', 'semimonthly'];

	let account = $state<BankAccount | null>(null);
	let loading = $state(true);
	let calculating = $state(false);
	let error = $state<string | null>(null);
	let forecast = $state<ForecastResponse | null>(null);
	let expanded = $state<Record<string, boolean>>({});

	let startingBalance = $state('0');
	let incomePerCycle = $state('0');
	let startDate = $state('');
	let endDate = $state('');
	let cycleType = $state<CycleType>('biweekly');

	function isoDate(date: Date): string {
		return date.toISOString().slice(0, 10);
	}

	onMount(async () => {
		loading = true;
		try {
			account = await getAccount(accountId);
			const today = new Date();
			const inNinetyDays = new Date(today);
			inNinetyDays.setDate(inNinetyDays.getDate() + 90);

			startingBalance =
				account.forecast_starting_balance_cents != null
					? (account.forecast_starting_balance_cents / 100).toString()
					: '0';
			incomePerCycle =
				account.forecast_income_per_cycle_cents != null
					? (account.forecast_income_per_cycle_cents / 100).toString()
					: '0';
			cycleType = account.forecast_cycle_type ?? 'biweekly';
			startDate = account.forecast_start_date ?? isoDate(today);
			endDate = account.forecast_end_date ?? isoDate(inNinetyDays);
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	});

	async function handleCalculate(event: SubmitEvent) {
		event.preventDefault();
		calculating = true;
		error = null;
		try {
			forecast = await computeForecast(accountId, {
				start_date: startDate,
				end_date: endDate,
				starting_balance_cents: Math.round(Number(startingBalance) * 100),
				income_per_cycle_cents: Math.round(Number(incomePerCycle) * 100),
				cycle_type: cycleType
			});
			expanded = {};
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			calculating = false;
		}
	}

	function toggleExpanded(cycleStart: string) {
		expanded = { ...expanded, [cycleStart]: !expanded[cycleStart] };
	}

	function handleRowKeydown(event: KeyboardEvent, cycleStart: string) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			toggleExpanded(cycleStart);
		}
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	function rowClass(runningBalanceCents: number): string {
		if (runningBalanceCents < 0) return 'bg-red-600 text-white';
		if (runningBalanceCents <= 10000) return 'bg-slate-200';
		return '';
	}
</script>

<a class="text-sm text-primary underline" href="/accounts/{accountId}">&larr; Bills</a>
<h1 class="mt-2 text-2xl font-semibold text-text">
	Forecast{#if account}
		({account.name}{#if account.institution} - {account.institution}{/if}){/if}
</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCalculate}>
		<Input label="Starting balance ($)" type="number" bind:value={startingBalance} required />
		<Input label="Income per cycle ($)" type="number" bind:value={incomePerCycle} required />
		<DatePicker label="Start date" bind:value={startDate} />
		<DatePicker label="End date" bind:value={endDate} />
		<Select label="Cycle" bind:value={cycleType}>
			{#each cycleTypeOptions as option (option)}
				<option value={option}>{cycleTypeLabels[option]}</option>
			{/each}
		</Select>
		<Button type="submit" disabled={calculating || loading}>Calculate</Button>
	</form>
</Card>

{#if forecast}
	{#if forecast.unscheduled_bills.length > 0}
		<p class="mt-4 rounded-card bg-amber-50 px-4 py-2 text-sm text-amber-800">
			{forecast.unscheduled_bills.length} bill{forecast.unscheduled_bills.length === 1
				? ''
				: 's'} couldn't be included - missing recurrence configuration:
			{forecast.unscheduled_bills.map((bill) => bill.name).join(', ')}
		</p>
	{/if}

	<div class="mt-6">
		<Table>
			<thead>
				<tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
					<th class="px-4 py-2 font-medium" colspan="2">Pay period</th>
					<th class="px-4 py-2 text-right font-medium">Balance</th>
				</tr>
			</thead>
			<tbody>
				{#each forecast.cycles as cycle (cycle.start_date)}
					{@const clickable = cycle.bills.length > 0}
					<tr
						class="border-b border-slate-100 last:border-0 {clickable
							? 'cursor-pointer'
							: ''} {rowClass(cycle.running_balance_cents)}"
						role={clickable ? 'button' : undefined}
						tabindex={clickable ? 0 : undefined}
						onclick={() => clickable && toggleExpanded(cycle.start_date)}
						onkeydown={(event) => clickable && handleRowKeydown(event, cycle.start_date)}
					>
						<td class="px-4 py-2" colspan="2">{cycle.start_date} - {cycle.end_date}</td>
						<td class="px-4 py-2 text-right">{formatAmount(cycle.running_balance_cents)}</td>
					</tr>
					{#if expanded[cycle.start_date]}
						{#each cycle.bills as bill (bill.bill_id + bill.due_date)}
							<tr class="border-b border-slate-100 text-sm text-slate-600 last:border-0">
								<td class="px-4 py-2 pl-8">{bill.due_date}</td>
								<td class="px-4 py-2">{bill.name}</td>
								<td class="px-4 py-2 text-right">{formatAmount(bill.amount_cents)}</td>
							</tr>
						{/each}
					{/if}
				{/each}
			</tbody>
		</Table>
	</div>
{/if}
