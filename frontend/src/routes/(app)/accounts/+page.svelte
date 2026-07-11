<script lang="ts">
	import { createAccount, deleteAccount, listAccounts } from '$lib/api/accounts';
	import type { BankAccount } from '$lib/api/types';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import Input from '$lib/components/Input.svelte';
	import Table from '$lib/components/Table.svelte';
	import { onMount } from 'svelte';

	let accounts = $state<BankAccount[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let name = $state('');
	let institution = $state('');
	let creating = $state(false);

	async function load() {
		loading = true;
		error = null;
		try {
			accounts = await listAccounts();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			loading = false;
		}
	}

	onMount(load);

	async function handleCreate(event: SubmitEvent) {
		event.preventDefault();
		if (!name.trim()) return;
		creating = true;
		try {
			await createAccount({ name, institution: institution || null });
			name = '';
			institution = '';
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}

	async function handleDelete(id: number) {
		try {
			await deleteAccount(id);
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	}
</script>

<h1 class="text-2xl font-semibold text-text">Accounts</h1>

{#if error}
	<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

<Card>
	<form class="flex flex-wrap items-end gap-4" onsubmit={handleCreate}>
		<Input label="Name" bind:value={name} placeholder="Checking" required />
		<Input label="Institution" bind:value={institution} placeholder="Bank (optional)" />
		<Button type="submit" disabled={creating}>Add account</Button>
	</form>
</Card>

<div class="mt-6">
	{#if loading}
		<p class="text-sm text-slate-500">Loading...</p>
	{:else if accounts.length === 0}
		<p class="text-sm text-slate-500">No accounts yet.</p>
	{:else}
		<Table>
			<thead>
				<tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
					<th class="px-4 py-2 font-medium">Name</th>
					<th class="px-4 py-2 font-medium">Institution</th>
					<th class="px-4 py-2"></th>
				</tr>
			</thead>
			<tbody>
				{#each accounts as account (account.id)}
					<tr class="border-b border-slate-100 last:border-0">
						<td class="px-4 py-2">
							<a class="text-primary underline" href="/accounts/{account.id}">{account.name}</a>
						</td>
						<td class="px-4 py-2 text-slate-600">{account.institution ?? '—'}</td>
						<td class="px-4 py-2 text-right">
							<Button variant="danger" onclick={() => handleDelete(account.id)}>Delete</Button>
						</td>
					</tr>
				{/each}
			</tbody>
		</Table>
	{/if}
</div>
