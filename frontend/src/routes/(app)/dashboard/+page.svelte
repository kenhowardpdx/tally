<script lang="ts">
	import { apiFetch } from '$lib/api';
	import { getDashboard } from '$lib/api/dashboard';
	import type { DashboardAccountSummary, DashboardResponse } from '$lib/api/types';
	import Card from '$lib/components/Card.svelte';
	import { cycleTypeLabels } from '$lib/cycle';
	import { onMount } from 'svelte';

	let dashboard = $state<DashboardResponse | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function load() {
		loading = true;
		error = null;
		try {
			dashboard = await getDashboard();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	}

	onMount(load);

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	function balanceClass(cents: number): string {
		if (cents < 0) return 'text-red-700';
		if (cents <= 10000) return 'text-amber-700';
		return 'text-emerald-700';
	}

	function dueCount(summary: DashboardAccountSummary): number {
		return summary.bills.length + summary.windfalls.length;
	}

	// Dev-only manual check that round-trips a real access token through the
	// backend's JWT validation - gated below so it never ships to real users.
	let meResult = $state<string | null>(null);
	async function checkBackendAuth() {
		meResult = 'Loading...';
		try {
			const res = await apiFetch('/api/v1/me');
			meResult = res.ok ? JSON.stringify(await res.json()) : `Error: HTTP ${res.status}`;
		} catch (err) {
			meResult = `Error: ${err instanceof Error ? err.message : String(err)}`;
		}
	}
</script>

<h1 class="text-2xl font-semibold text-text">Dashboard</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

{#if loading}
	<div class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true">
		{#each Array(3) as _, i (i)}
			<div class="h-40 animate-pulse rounded-card bg-slate-100"></div>
		{/each}
	</div>
{:else if !dashboard || dashboard.accounts.length === 0}
	<Card>
		<p class="text-sm text-slate-600">
			No accounts yet. <a class="text-primary underline" href="/accounts">Add a bank account</a> to
			start tracking bills and forecasting your balance.
		</p>
	</Card>
{:else}
	<div class="mt-2">
		<span class="text-sm text-slate-500">Combined balance across current cycles</span>
		<p class="text-3xl font-semibold {balanceClass(dashboard.combined_ending_balance_cents)}">
			{formatAmount(dashboard.combined_ending_balance_cents)}
		</p>
	</div>

	<div class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each dashboard.accounts as summary (summary.account_id)}
			<Card>
				<div class="flex items-start justify-between gap-2">
					<h2 class="font-semibold text-text">
						{summary.account_name}
						{#if summary.institution}
							<span class="font-normal text-slate-500">- {summary.institution}</span>
						{/if}
					</h2>
					{#if summary.configured}
						<span
							class="inline-flex shrink-0 items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
						>
							{summary.is_upcoming ? 'Upcoming' : 'Current cycle'}
						</span>
					{/if}
				</div>

				{#if !summary.configured}
					<p class="mt-3 text-sm text-slate-500">No forecast has been run for this account yet.</p>
					<a
						class="mt-3 inline-block text-sm text-primary underline"
						href="/accounts/{summary.account_id}/forecast"
					>
						Run a forecast &rarr;
					</a>
				{:else}
					<p class="mt-2 text-xs text-slate-500">
						{cycleTypeLabels[summary.cycle_type!]} &middot; {summary.cycle_start_date} - {summary.cycle_end_date}
					</p>
					<p class="mt-3 text-2xl font-semibold {balanceClass(summary.ending_balance_cents!)}">
						{formatAmount(summary.ending_balance_cents!)}
					</p>
					<p class="text-xs text-slate-500">
						{dueCount(summary)} item{dueCount(summary) === 1 ? '' : 's'} in this cycle
					</p>
					<a
						class="mt-3 inline-block text-sm text-primary underline"
						href="/accounts/{summary.account_id}/forecast"
					>
						View forecast &rarr;
					</a>
				{/if}
			</Card>
		{/each}
	</div>
{/if}

{#if import.meta.env.DEV}
	<button
		class="mt-8 rounded-card border border-slate-300 px-3 py-1.5 text-sm text-text hover:bg-slate-50"
		onclick={checkBackendAuth}
	>
		Test backend auth (GET /api/v1/me)
	</button>
	{#if meResult}
		<pre class="mt-2 rounded-card bg-slate-100 p-3 text-xs">{meResult}</pre>
	{/if}
{/if}
