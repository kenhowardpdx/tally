<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount } from '$lib/api/accounts';
	import { upsertCycleOverride } from '$lib/api/cycle-overrides';
	import { computeForecast } from '$lib/api/forecast';
	import type {
		BankAccount,
		CycleType,
		ForecastBillLine,
		ForecastCycle,
		ForecastRequest,
		ForecastResponse,
		ForecastWindfallLine
	} from '$lib/api/types';
	import { accountSuffix } from '$lib/format';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import Input from '$lib/components/Input.svelte';
	import Select from '$lib/components/Select.svelte';
	import Table from '$lib/components/Table.svelte';
	import { cycleTypeLabels } from '$lib/cycle';
	import { glossaryTerms } from '$lib/glossary';
	import { onMount } from 'svelte';

	const cycleTooltip = glossaryTerms.find((t) => t.term === 'Cycle type')!.definition;

	const accountId = $derived(Number($page.params.id));

	const cycleTypeOptions: CycleType[] = ['weekly', 'biweekly', 'monthly', 'semimonthly'];

	let account = $state<BankAccount | null>(null);
	let loading = $state(true);
	let calculating = $state(false);
	let error = $state<string | null>(null);
	let forecast = $state<ForecastResponse | null>(null);
	let expanded = $state<Record<string, boolean>>({});
	let reconciliationExpanded = $state<Record<string, boolean>>({});
	let lastForecastRequest = $state<ForecastRequest | null>(null);

	let startingBalance = $state('0');
	let incomePerCycle = $state('0');
	let startDate = $state('');
	let endDate = $state('');
	let cycleType = $state<CycleType>('biweekly');

	function isoDate(date: Date): string {
		// Local date components, not toISOString() (which formats in UTC and
		// can shift the day relative to the user's local time) - matches
		// DatePicker's own toISO() so defaults and picked dates agree.
		const year = date.getFullYear();
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

	const today = isoDate(new Date());

	// The active cycle is the one currently in progress - the only one
	// where reconciliation controls make sense (past cycles are closed
	// books, future ones haven't happened yet).
	function isActiveCycle(cycle: ForecastCycle): boolean {
		return cycle.start_date <= today && today < cycle.end_date;
	}

	onMount(async () => {
		loading = true;
		try {
			account = await getAccount(accountId);
			const inNinetyDays = new Date();
			inNinetyDays.setDate(inNinetyDays.getDate() + 90);

			const hasSavedForecastSettings =
				account.forecast_starting_balance_cents != null &&
				account.forecast_start_date != null &&
				account.forecast_end_date != null;

			startingBalance =
				account.forecast_starting_balance_cents != null
					? (account.forecast_starting_balance_cents / 100).toString()
					: '0';
			incomePerCycle =
				account.forecast_income_per_cycle_cents != null
					? (account.forecast_income_per_cycle_cents / 100).toString()
					: '0';
			cycleType = account.forecast_cycle_type ?? 'biweekly';
			startDate = account.forecast_start_date ?? today;
			endDate = account.forecast_end_date ?? isoDate(inNinetyDays);

			if (hasSavedForecastSettings) {
				await calculate();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	});

	async function calculate() {
		const startingBalanceCents = Math.round(Number(startingBalance) * 100);
		const incomePerCycleCents = Math.round(Number(incomePerCycle) * 100);
		if (
			!startDate ||
			!endDate ||
			Number.isNaN(startingBalanceCents) ||
			Number.isNaN(incomePerCycleCents)
		) {
			return;
		}
		calculating = true;
		error = null;
		try {
			lastForecastRequest = {
				start_date: startDate,
				end_date: endDate,
				starting_balance_cents: startingBalanceCents,
				income_per_cycle_cents: incomePerCycleCents,
				cycle_type: cycleType
			};
			forecast = await computeForecast(accountId, lastForecastRequest);
			expanded = {};
			reconciliationExpanded = {};
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			calculating = false;
		}
	}

	async function handleCalculate(event: SubmitEvent) {
		event.preventDefault();
		await calculate();
	}

	// Cycle overrides can shift a cycle's net_cents, which cascades into every
	// later cycle's running_balance_cents - re-running the same forecast
	// request through the real engine keeps that math authoritative instead
	// of re-deriving cascading balances client-side.
	async function refreshForecast() {
		if (!lastForecastRequest) return;
		forecast = await computeForecast(accountId, lastForecastRequest);
	}

	function toggleExpanded(cycleStart: string) {
		expanded = { ...expanded, [cycleStart]: !expanded[cycleStart] };
	}

	function toggleReconciliation(cycleStart: string) {
		reconciliationExpanded = {
			...reconciliationExpanded,
			[cycleStart]: !reconciliationExpanded[cycleStart]
		};
	}

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	function rowClass(runningBalanceCents: number): string {
		if (runningBalanceCents < 0) return 'bg-red-600 text-white';
		if (runningBalanceCents <= 10000) return 'bg-slate-200';
		return '';
	}

	async function saveOverride(params: {
		billId?: number;
		windfallId?: number;
		cycleStartDate: string;
		completed: boolean;
		overrideAmountCents: number | null;
		notes: string | null;
	}) {
		error = null;
		try {
			await upsertCycleOverride({
				account_id: accountId,
				bill_id: params.billId ?? null,
				windfall_id: params.windfallId ?? null,
				cycle_start_date: params.cycleStartDate,
				completed: params.completed,
				override_amount_cents: params.overrideAmountCents,
				notes: params.notes
			});
			await refreshForecast();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}

	function currentOverrideAmount(line: { amount_cents: number; forecasted_amount_cents: number }) {
		return line.amount_cents !== line.forecasted_amount_cents ? line.amount_cents : null;
	}

	function toggleBillCompleted(cycle: ForecastCycle, line: ForecastBillLine) {
		saveOverride({
			billId: line.bill_id,
			cycleStartDate: cycle.start_date,
			completed: !line.completed,
			overrideAmountCents: currentOverrideAmount(line),
			notes: line.notes
		});
	}

	function commitBillAmount(cycle: ForecastCycle, line: ForecastBillLine, event: Event) {
		const raw = (event.target as HTMLInputElement).value.trim();
		const cents = raw === '' ? null : Math.round(Number(raw) * 100);
		saveOverride({
			billId: line.bill_id,
			cycleStartDate: cycle.start_date,
			completed: line.completed,
			overrideAmountCents: cents !== null && Number.isNaN(cents) ? null : cents,
			notes: line.notes
		});
	}

	function resetBillAmount(cycle: ForecastCycle, line: ForecastBillLine) {
		saveOverride({
			billId: line.bill_id,
			cycleStartDate: cycle.start_date,
			completed: line.completed,
			overrideAmountCents: null,
			notes: line.notes
		});
	}

	function commitBillNotes(cycle: ForecastCycle, line: ForecastBillLine, event: Event) {
		const raw = (event.target as HTMLInputElement).value.trim();
		saveOverride({
			billId: line.bill_id,
			cycleStartDate: cycle.start_date,
			completed: line.completed,
			overrideAmountCents: currentOverrideAmount(line),
			notes: raw === '' ? null : raw
		});
	}

	function toggleWindfallCompleted(cycle: ForecastCycle, line: ForecastWindfallLine) {
		saveOverride({
			windfallId: line.windfall_id,
			cycleStartDate: cycle.start_date,
			completed: !line.completed,
			overrideAmountCents: currentOverrideAmount(line),
			notes: line.notes
		});
	}

	function commitWindfallAmount(cycle: ForecastCycle, line: ForecastWindfallLine, event: Event) {
		const raw = (event.target as HTMLInputElement).value.trim();
		const cents = raw === '' ? null : Math.round(Number(raw) * 100);
		saveOverride({
			windfallId: line.windfall_id,
			cycleStartDate: cycle.start_date,
			completed: line.completed,
			overrideAmountCents: cents !== null && Number.isNaN(cents) ? null : cents,
			notes: line.notes
		});
	}

	function resetWindfallAmount(cycle: ForecastCycle, line: ForecastWindfallLine) {
		saveOverride({
			windfallId: line.windfall_id,
			cycleStartDate: cycle.start_date,
			completed: line.completed,
			overrideAmountCents: null,
			notes: line.notes
		});
	}

	function commitWindfallNotes(cycle: ForecastCycle, line: ForecastWindfallLine, event: Event) {
		const raw = (event.target as HTMLInputElement).value.trim();
		saveOverride({
			windfallId: line.windfall_id,
			cycleStartDate: cycle.start_date,
			completed: line.completed,
			overrideAmountCents: currentOverrideAmount(line),
			notes: raw === '' ? null : raw
		});
	}

	// Forecasted total vs. sum-of-actuals (using override amounts where set,
	// base amounts where not) for the active cycle - cycle.net_cents from the
	// backend is already the "actual" side, since build_cycle substitutes
	// override amounts before summing.
	function reconciliation(cycle: ForecastCycle) {
		const forecastedBills = cycle.bills.reduce((sum, b) => sum + b.forecasted_amount_cents, 0);
		const forecastedWindfalls = cycle.windfalls.reduce(
			(sum, w) => sum + w.forecasted_amount_cents,
			0
		);
		const forecastedTransactions = cycle.transactions.reduce((sum, t) => sum + t.amount_cents, 0);
		const forecastedNetCents = forecastedWindfalls + forecastedTransactions - forecastedBills;
		const actualNetCents = cycle.net_cents;
		return {
			forecastedNetCents,
			actualNetCents,
			varianceCents: actualNetCents - forecastedNetCents
		};
	}
</script>

<AccountNav {accountId} current="forecast" />
<h1 class="mt-2 text-2xl font-semibold text-text">
	Forecast{accountSuffix(account)}
</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

{#if loading}
	<p class="mt-4 text-sm text-slate-500">Loading account...</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCalculate}>
		<Input
			label="Starting balance ($)"
			type="number"
			step="0.01"
			bind:value={startingBalance}
			required
		/>
		<Input
			label="Income per cycle ($)"
			type="number"
			step="0.01"
			bind:value={incomePerCycle}
			required
		/>
		<DatePicker label="Start date" bind:value={startDate} />
		<DatePicker label="End date" bind:value={endDate} />
		<Select
			label="Cycle"
			bind:value={cycleType}
			options={cycleTypeOptions.map((option) => ({ value: option, label: cycleTypeLabels[option] }))}
			tooltip={cycleTooltip}
		/>
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
					{@const clickable =
						cycle.bills.length > 0 || cycle.transactions.length > 0 || cycle.windfalls.length > 0}
					{@const active = isActiveCycle(cycle)}
					<tr class="border-b border-slate-100 last:border-0 {rowClass(cycle.running_balance_cents)}">
						{#if clickable}
							<td class="p-0" colspan="3">
								<button
									type="button"
									class="flex w-full cursor-pointer items-center justify-between px-4 py-2 text-left"
									onclick={() => toggleExpanded(cycle.start_date)}
									aria-expanded={!!expanded[cycle.start_date]}
								>
									<span>
										{cycle.start_date} - {cycle.end_date}
										{#if active}
											<span
												class="ml-2 inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
											>
												Current cycle
											</span>
										{/if}
									</span>
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
							{#if active}
								<tr class="border-b border-slate-100 text-sm text-slate-600 last:border-0">
									<td class="px-4 py-2 pl-8" colspan="3">
										<div class="flex flex-wrap items-center gap-x-3 gap-y-1">
											<label class="flex items-center gap-2">
												<input
													type="checkbox"
													checked={bill.completed}
													onchange={() => toggleBillCompleted(cycle, bill)}
													aria-label="Paid"
												/>
												<span class="w-16 shrink-0 text-xs text-slate-400">{bill.due_date}</span>
												<span class={bill.completed ? 'text-slate-400 line-through' : 'text-text'}>
													{bill.name}
												</span>
											</label>
											<div class="ml-auto flex items-center gap-2">
												<span class="text-xs text-slate-400">$</span>
												<input
													type="text"
													inputmode="decimal"
													placeholder={(bill.forecasted_amount_cents / 100).toString()}
													value={currentOverrideAmount(bill) !== null
														? (bill.amount_cents / 100).toString()
														: ''}
													onchange={(event) => commitBillAmount(cycle, bill, event)}
													class="w-20 rounded-card border border-slate-300 px-2 py-1 text-right text-xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
												/>
												{#if currentOverrideAmount(bill) !== null}
													<button
														type="button"
														class="text-xs text-slate-400 underline hover:text-primary"
														onclick={() => resetBillAmount(cycle, bill)}
													>
														Reset
													</button>
												{/if}
												<input
													type="text"
													placeholder="Note"
													value={bill.notes ?? ''}
													onchange={(event) => commitBillNotes(cycle, bill, event)}
													class="w-28 rounded-card border border-slate-300 px-2 py-1 text-xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
												/>
											</div>
										</div>
									</td>
								</tr>
							{:else}
								<tr class="border-b border-slate-100 text-sm text-slate-600 last:border-0">
									<td class="px-4 py-2 pl-8 align-top">{bill.due_date}</td>
									<td class="px-4 py-2 align-top {bill.completed ? 'text-slate-400 line-through' : ''}">
										{bill.name}
									</td>
									<td class="px-4 py-2 text-right align-top">
										{formatAmount(bill.amount_cents)}
										{#if bill.notes}
											<p class="text-xs text-slate-400">{bill.notes}</p>
										{/if}
									</td>
								</tr>
							{/if}
						{/each}
						{#each cycle.transactions as transaction (`transaction-${transaction.transaction_id}`)}
							<tr class="border-b border-slate-100 text-sm text-slate-600 last:border-0">
								<td class="px-4 py-2 pl-8">{transaction.date}</td>
								<td class="px-4 py-2">{transaction.description ?? 'Transaction'}</td>
								<td
									class="px-4 py-2 text-right {transaction.amount_cents < 0
										? 'text-red-700'
										: 'text-emerald-700'}"
								>
									{formatAmount(transaction.amount_cents)}
								</td>
							</tr>
						{/each}
						{#each cycle.windfalls as windfall (`windfall-${windfall.windfall_id}`)}
							{#if active}
								<tr class="border-b border-slate-100 text-sm text-slate-600 last:border-0">
									<td class="px-4 py-2 pl-8" colspan="3">
										<div class="flex flex-wrap items-center gap-x-3 gap-y-1">
											<label class="flex items-center gap-2">
												<input
													type="checkbox"
													checked={windfall.completed}
													onchange={() => toggleWindfallCompleted(cycle, windfall)}
													aria-label="Received"
												/>
												<span class="w-16 shrink-0 text-xs text-slate-400">{windfall.expected_date}</span>
												<span
													class="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
												>
													Windfall
												</span>
												<span
													class={windfall.completed ? 'text-slate-400 line-through' : 'text-text'}
												>
													{windfall.name}
												</span>
											</label>
											<div class="ml-auto flex items-center gap-2">
												<span class="text-xs text-slate-400">$</span>
												<input
													type="text"
													inputmode="decimal"
													placeholder={(windfall.forecasted_amount_cents / 100).toString()}
													value={currentOverrideAmount(windfall) !== null
														? (windfall.amount_cents / 100).toString()
														: ''}
													onchange={(event) => commitWindfallAmount(cycle, windfall, event)}
													class="w-20 rounded-card border border-slate-300 px-2 py-1 text-right text-xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
												/>
												{#if currentOverrideAmount(windfall) !== null}
													<button
														type="button"
														class="text-xs text-slate-400 underline hover:text-primary"
														onclick={() => resetWindfallAmount(cycle, windfall)}
													>
														Reset
													</button>
												{/if}
												<input
													type="text"
													placeholder="Note"
													value={windfall.notes ?? ''}
													onchange={(event) => commitWindfallNotes(cycle, windfall, event)}
													class="w-28 rounded-card border border-slate-300 px-2 py-1 text-xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
												/>
											</div>
										</div>
									</td>
								</tr>
							{:else}
								<tr class="border-b border-slate-100 text-sm text-slate-600 last:border-0">
									<td class="px-4 py-2 pl-8 align-top">{windfall.expected_date}</td>
									<td class="px-4 py-2 align-top {windfall.completed ? 'text-slate-400 line-through' : ''}">
										<span
											class="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
										>
											Windfall
										</span>
										{windfall.name}
									</td>
									<td class="px-4 py-2 text-right align-top">
										<span class="text-emerald-700">{formatAmount(windfall.amount_cents)}</span>
										{#if windfall.notes}
											<p class="text-xs text-slate-400">{windfall.notes}</p>
										{/if}
									</td>
								</tr>
							{/if}
						{/each}
						{#if active}
							{@const summary = reconciliation(cycle)}
							<tr class="border-b border-slate-200 bg-slate-50 text-sm text-slate-700 last:border-0">
								<td class="p-0" colspan="3">
									<button
										type="button"
										class="flex w-full items-center justify-between px-4 py-2 pl-8 text-left font-medium"
										onclick={() => toggleReconciliation(cycle.start_date)}
										aria-expanded={!!reconciliationExpanded[cycle.start_date]}
									>
										<span>Reconciliation - forecasted vs. actual</span>
										<span
											class={summary.varianceCents === 0
												? 'text-slate-500'
												: summary.varianceCents > 0
													? 'text-emerald-700'
													: 'text-red-700'}
										>
											Variance: {formatAmount(summary.varianceCents)}
										</span>
									</button>
									{#if reconciliationExpanded[cycle.start_date]}
										<div class="flex justify-end gap-4 px-4 pb-2 pl-8 text-xs text-slate-500">
											<span>Forecasted: {formatAmount(summary.forecastedNetCents)}</span>
											<span>Actual: {formatAmount(summary.actualNetCents)}</span>
										</div>
									{/if}
								</td>
							</tr>
						{/if}
					{/if}
				{/each}
			</tbody>
		</Table>
	</div>
{/if}
