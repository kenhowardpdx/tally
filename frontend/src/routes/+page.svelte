<script lang="ts">
	import { goto } from '$app/navigation';
	import { computeDemoForecast } from '$lib/api/demo';
	import type { DemoBill, ForecastResponse } from '$lib/api/types';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import Input from '$lib/components/Input.svelte';
	import Select from '$lib/components/Select.svelte';
	import Table from '$lib/components/Table.svelte';
	import { isAuthenticated, isLoading, login } from '$lib/auth';
	import { recurrenceLabels } from '$lib/recurrence';

	$effect(() => {
		if (!$isLoading && $isAuthenticated) goto('/accounts');
	});

	function isoDate(date: Date): string {
		const year = date.getFullYear();
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

	const today = isoDate(new Date());

	// Recurrence types that need no extra recurrence_config - the only ones
	// the demo's simple add-bill form supports (semimonthly/custom_days need
	// per-type fields RecurrenceConfigFields.svelte handles for real bills,
	// more than a logged-out preview widget needs).
	const demoRecurrenceOptions: DemoBill['recurrence_type'][] = [
		'weekly',
		'biweekly',
		'monthly',
		'annually'
	];

	let nextId = 4;
	let demoBills = $state<DemoBill[]>([
		{ id: 1, name: 'Rent', amount_cents: 150000, recurrence_type: 'monthly', start_date: today },
		{
			id: 2,
			name: 'Car payment',
			amount_cents: 35000,
			recurrence_type: 'monthly',
			start_date: today
		},
		{ id: 3, name: 'Streaming', amount_cents: 1500, recurrence_type: 'monthly', start_date: today }
	]);

	let newBillName = $state('');
	let newBillAmount = $state('');
	let newBillRecurrence = $state<DemoBill['recurrence_type']>('monthly');

	let startingBalance = $state('2000');
	let incomePerCycle = $state('1200');
	let cycleType = $state<'weekly' | 'biweekly' | 'monthly'>('biweekly');

	let forecast = $state<ForecastResponse | null>(null);
	let calculating = $state(false);
	let error = $state<string | null>(null);
	let expanded = $state<Record<string, boolean>>({});

	function addDemoBill(event: SubmitEvent) {
		event.preventDefault();
		const cents = Math.round(Number(newBillAmount) * 100);
		if (!newBillName.trim() || Number.isNaN(cents) || cents <= 0) return;
		demoBills = [
			...demoBills,
			{
				id: nextId++,
				name: newBillName,
				amount_cents: cents,
				recurrence_type: newBillRecurrence,
				start_date: today
			}
		];
		newBillName = '';
		newBillAmount = '';
	}

	function removeDemoBill(id: number) {
		demoBills = demoBills.filter((bill) => bill.id !== id);
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	async function runDemo() {
		const startingBalanceCents = Math.round(Number(startingBalance) * 100);
		const incomePerCycleCents = Math.round(Number(incomePerCycle) * 100);
		if (Number.isNaN(startingBalanceCents) || Number.isNaN(incomePerCycleCents)) return;

		calculating = true;
		error = null;
		try {
			const inNinetyDays = new Date();
			inNinetyDays.setDate(inNinetyDays.getDate() + 90);
			forecast = await computeDemoForecast({
				bills: demoBills,
				cycle_type: cycleType,
				start_date: today,
				end_date: isoDate(inNinetyDays),
				starting_balance_cents: startingBalanceCents,
				income_per_cycle_cents: incomePerCycleCents
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

	function rowClass(runningBalanceCents: number): string {
		if (runningBalanceCents < 0) return 'bg-red-600 text-white';
		if (runningBalanceCents <= 10000) return 'bg-slate-200';
		return '';
	}
</script>

{#if !$isLoading && !$isAuthenticated}
	<section class="py-12 text-center">
		<h1 class="text-4xl font-bold text-text">Know your balance before the bills hit.</h1>
		<p class="mx-auto mt-4 max-w-xl text-lg text-slate-600">
			Tally tracks your recurring bills and forecasts your bank balance cycle by cycle, so
			surprises show up on a screen instead of a bounced payment.
		</p>
		<div class="mt-6 flex flex-wrap justify-center gap-3">
			<Button onclick={() => login()}>Log in to get started</Button>
			<a
				href="#demo"
				class="rounded-card border border-slate-300 px-4 py-2 text-sm font-medium text-text hover:bg-slate-50"
			>
				Try the demo below
			</a>
		</div>
	</section>

	<section class="grid grid-cols-1 gap-4 py-6 sm:grid-cols-3">
		<Card>
			<h2 class="font-semibold text-text">Recurring bills, any cadence</h2>
			<p class="mt-2 text-sm text-slate-600">
				Weekly, biweekly, semimonthly (10th &amp; 25th), monthly, annually, or a custom interval -
				enable or disable a bill without deleting it.
			</p>
		</Card>
		<Card>
			<h2 class="font-semibold text-text">Cycle-by-cycle forecasting</h2>
			<p class="mt-2 text-sm text-slate-600">
				See your running balance for every upcoming pay cycle, with one-off transactions and
				windfalls (bonuses, refunds) folded in.
			</p>
		</Card>
		<Card>
			<h2 class="font-semibold text-text">Reconcile as you go</h2>
			<p class="mt-2 text-sm text-slate-600">
				Mark a bill paid, adjust its actual amount for one cycle, and compare forecasted vs.
				actual - without touching the bill's normal amount.
			</p>
		</Card>
	</section>

	<section id="demo" class="py-8">
		<h2 class="text-2xl font-semibold text-text">Try it - no login required</h2>
		<p class="mt-2 text-slate-600">
			Add or remove a few sample bills and calculate a forecast. This runs the same forecasting
			engine as the real app, just against sample data that's never saved.
		</p>

		{#if error}
			<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
		{/if}

		<Card>
			<h3 class="text-sm font-semibold text-text">Sample bills</h3>
			<div class="mt-3 overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
							<th class="py-1.5 pr-2 font-medium">Name</th>
							<th class="py-1.5 pr-2 font-medium">Amount</th>
							<th class="py-1.5 pr-2 font-medium">Frequency</th>
							<th class="py-1.5"></th>
						</tr>
					</thead>
					<tbody>
						{#each demoBills as bill (bill.id)}
							<tr class="border-b border-slate-100 last:border-0">
								<td class="py-1.5 pr-2">{bill.name}</td>
								<td class="py-1.5 pr-2">{formatAmount(bill.amount_cents)}</td>
								<td class="py-1.5 pr-2 text-slate-600">{recurrenceLabels[bill.recurrence_type]}</td>
								<td class="py-1.5 text-right">
									<button
										type="button"
										class="text-xs text-red-700 underline"
										onclick={() => removeDemoBill(bill.id)}
									>
										Remove
									</button>
								</td>
							</tr>
						{/each}
						{#if demoBills.length === 0}
							<tr><td class="py-3 text-slate-500" colspan="4">No bills - add one below.</td></tr>
						{/if}
					</tbody>
				</table>
			</div>

			<form class="mt-4 flex flex-wrap items-end gap-3" onsubmit={addDemoBill}>
				<Input label="Bill name" bind:value={newBillName} placeholder="Gym membership" />
				<Input label="Amount ($)" type="number" step="0.01" bind:value={newBillAmount} />
				<Select
					label="Frequency"
					bind:value={newBillRecurrence}
					options={demoRecurrenceOptions.map((option) => ({
						value: option,
						label: recurrenceLabels[option]
					}))}
				/>
				<Button type="submit" variant="secondary">Add bill</Button>
			</form>
		</Card>

		<Card>
			<form
				class="flex flex-wrap items-end gap-4"
				onsubmit={(event) => {
					event.preventDefault();
					runDemo();
				}}
			>
				<Input label="Starting balance ($)" type="number" step="0.01" bind:value={startingBalance} />
				<Input label="Income per cycle ($)" type="number" step="0.01" bind:value={incomePerCycle} />
				<Select
					label="Cycle"
					bind:value={cycleType}
					options={[
						{ value: 'weekly', label: 'Weekly' },
						{ value: 'biweekly', label: 'Biweekly' },
						{ value: 'monthly', label: 'Monthly' }
					]}
				/>
				<Button type="submit" disabled={calculating}>
					{calculating ? 'Calculating...' : 'Calculate forecast'}
				</Button>
			</form>
		</Card>

		{#if forecast}
			{#if forecast.unscheduled_bills.length > 0}
				<p class="mt-4 rounded-card bg-amber-50 px-4 py-2 text-sm text-amber-800">
					{forecast.unscheduled_bills.length} bill{forecast.unscheduled_bills.length === 1
						? ''
						: 's'} couldn't be included.
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
								class="border-b border-slate-100 last:border-0 {rowClass(
									cycle.running_balance_cents
								)}"
							>
								{#if clickable}
									<td class="p-0" colspan="3">
										<button
											type="button"
											class="flex w-full cursor-pointer items-center justify-between px-4 py-2 text-left"
											onclick={() => toggleExpanded(cycle.start_date)}
											aria-expanded={!!expanded[cycle.start_date]}
										>
											<span>{cycle.start_date} - {cycle.end_date}</span>
											<span>{formatAmount(cycle.running_balance_cents)}</span>
										</button>
									</td>
								{:else}
									<td class="px-4 py-2" colspan="2">{cycle.start_date} - {cycle.end_date}</td>
									<td class="px-4 py-2 text-right">{formatAmount(cycle.running_balance_cents)}</td>
								{/if}
							</tr>
							{#if expanded[cycle.start_date]}
								{#each cycle.bills as bill (`bill-${bill.bill_id}-${bill.due_date}`)}
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

		<p class="mt-6 text-center text-sm text-slate-600">
			Like what you see?
			<button type="button" class="text-primary underline" onclick={() => login()}>
				Log in to track your real accounts.
			</button>
		</p>
	</section>
{/if}
