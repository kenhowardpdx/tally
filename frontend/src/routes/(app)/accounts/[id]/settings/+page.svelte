<script lang="ts">
	import { page } from '$app/stores';
	import { getAccount } from '$lib/api/accounts';
	import {
		commitBillImportCsv,
		exportBillsCsv,
		listBills,
		previewBillImportCsv
	} from '$lib/api/bills';
	import {
		commitTransactionImportCsv,
		exportTransactionsCsv,
		listTransactions,
		previewTransactionImportCsv
	} from '$lib/api/transactions';
	import {
		commitWindfallImportCsv,
		exportWindfallsCsv,
		previewWindfallImportCsv
	} from '$lib/api/windfalls';
	import { ApiError } from '$lib/api';
	import type {
		BankAccount,
		Bill,
		BillImportPreview,
		ImportRowIssue,
		Transaction,
		TransactionImportPreview,
		Windfall,
		WindfallImportPreview
	} from '$lib/api/types';
	import { accountSuffix } from '$lib/format';
	import AccountNav from '$lib/components/AccountNav.svelte';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import ImportPreviewModal from '$lib/components/ImportPreviewModal.svelte';
	import { onMount } from 'svelte';

	const accountId = $derived(Number($page.params.id));

	let account = $state<BankAccount | null>(null);

	onMount(() => {
		getAccount(accountId).then((a) => (account = a));
	});

	function formatMoney(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	function parseErrorsFrom(err: unknown): ImportRowIssue[] | null {
		if (
			err instanceof ApiError &&
			err.body &&
			typeof err.body === 'object' &&
			'detail' in err.body
		) {
			const detail = (err.body as { detail?: { errors?: ImportRowIssue[] } }).detail;
			if (detail?.errors) return detail.errors;
		}
		return null;
	}

	// ---------------------------------------------------------------------
	// Bills
	// ---------------------------------------------------------------------

	let billFileInput = $state<HTMLInputElement | undefined>();
	let billExporting = $state(false);
	let billPreviewLoading = $state(false);
	let billCommitting = $state(false);
	let billPreview = $state<BillImportPreview | null>(null);
	let billPreviewOpen = $state(false);
	let billParseErrors = $state<ImportRowIssue[] | null>(null);
	let billError = $state<string | null>(null);
	let currentBillsById = $state<Map<number, Bill>>(new Map());

	async function handleBillExport() {
		billExporting = true;
		billError = null;
		try {
			const blob = await exportBillsCsv(accountId);
			downloadBlob(blob, `bills-${accountId}.csv`);
		} catch (err) {
			billError = err instanceof Error ? err.message : String(err);
		} finally {
			billExporting = false;
		}
	}

	async function handleBillImportFile(event: Event) {
		const file = (event.target as HTMLInputElement).files?.[0];
		if (!file) return;
		billPreviewLoading = true;
		billError = null;
		billParseErrors = null;
		try {
			const [preview, current] = await Promise.all([
				previewBillImportCsv(accountId, file),
				listBills(accountId)
			]);
			billPreview = preview;
			currentBillsById = new Map(current.map((b) => [b.id, b]));
			billPreviewOpen = true;
		} catch (err) {
			const errors = parseErrorsFrom(err);
			if (errors) {
				billParseErrors = errors;
			} else {
				billError = err instanceof Error ? err.message : String(err);
			}
		} finally {
			billPreviewLoading = false;
			if (billFileInput) billFileInput.value = '';
		}
	}

	function summarizeNewBill(fields: BillImportPreview['new'][number]): string {
		return `${fields.name} (${formatMoney(fields.amount_cents)}, ${fields.recurrence_type})`;
	}

	function summarizeUpdatedBill(update: BillImportPreview['updated'][number]): string {
		const current = currentBillsById.get(update.id);
		if (!current) return update.fields.name;
		const changed: string[] = [];
		if ((current.notes ?? null) !== (update.fields.notes ?? null)) changed.push('notes');
		if ((current.end_date ?? null) !== (update.fields.end_date ?? null)) changed.push('end date');
		if (
			JSON.stringify(current.recurrence_config) !==
			JSON.stringify(update.fields.recurrence_config ?? {})
		) {
			changed.push('recurrence');
		}
		if (current.enabled !== (update.fields.enabled ?? true)) {
			changed.push(update.fields.enabled ? 're-enabled' : 'disabled');
		}
		return `${update.fields.name}${changed.length ? ' — ' + changed.join(', ') : ''}`;
	}

	function summarizeOmittedBill(bill: Bill): string {
		return `${bill.name} (${formatMoney(bill.amount_cents)})`;
	}

	async function handleBillCommit() {
		if (!billPreview) return;
		billCommitting = true;
		billError = null;
		try {
			await commitBillImportCsv(accountId, {
				new: billPreview.new,
				updated: billPreview.updated,
				omitted_ids: billPreview.omitted.map((b) => b.id)
			});
			billPreviewOpen = false;
			billPreview = null;
		} catch (err) {
			billError = err instanceof Error ? err.message : String(err);
		} finally {
			billCommitting = false;
		}
	}

	// ---------------------------------------------------------------------
	// Transactions
	// ---------------------------------------------------------------------

	let transactionFileInput = $state<HTMLInputElement | undefined>();
	let transactionExporting = $state(false);
	let transactionPreviewLoading = $state(false);
	let transactionCommitting = $state(false);
	let transactionPreview = $state<TransactionImportPreview | null>(null);
	let transactionPreviewOpen = $state(false);
	let transactionParseErrors = $state<ImportRowIssue[] | null>(null);
	let transactionError = $state<string | null>(null);
	let currentTransactionsById = $state<Map<number, Transaction>>(new Map());

	async function handleTransactionExport() {
		transactionExporting = true;
		transactionError = null;
		try {
			const blob = await exportTransactionsCsv(accountId);
			downloadBlob(blob, `transactions-${accountId}.csv`);
		} catch (err) {
			transactionError = err instanceof Error ? err.message : String(err);
		} finally {
			transactionExporting = false;
		}
	}

	async function handleTransactionImportFile(event: Event) {
		const file = (event.target as HTMLInputElement).files?.[0];
		if (!file) return;
		transactionPreviewLoading = true;
		transactionError = null;
		transactionParseErrors = null;
		try {
			const [preview, current] = await Promise.all([
				previewTransactionImportCsv(accountId, file),
				listTransactions(accountId)
			]);
			transactionPreview = preview;
			currentTransactionsById = new Map(current.map((t) => [t.id, t]));
			transactionPreviewOpen = true;
		} catch (err) {
			const errors = parseErrorsFrom(err);
			if (errors) {
				transactionParseErrors = errors;
			} else {
				transactionError = err instanceof Error ? err.message : String(err);
			}
		} finally {
			transactionPreviewLoading = false;
			if (transactionFileInput) transactionFileInput.value = '';
		}
	}

	function summarizeNewTransaction(fields: TransactionImportPreview['new'][number]): string {
		return `${formatMoney(fields.amount_cents)} on ${fields.date}${fields.description ? ` (${fields.description})` : ''}`;
	}

	function summarizeUpdatedTransaction(
		update: TransactionImportPreview['updated'][number]
	): string {
		const current = currentTransactionsById.get(update.id);
		const label = `${formatMoney(update.fields.amount_cents)} on ${update.fields.date}`;
		if (!current) return label;
		return `${label} — bill link ${update.fields.bill_id ? 'set' : 'cleared'}`;
	}

	function summarizeOmittedTransaction(transaction: Transaction): string {
		return `${formatMoney(transaction.amount_cents)} on ${transaction.date}${
			transaction.description ? ` (${transaction.description})` : ''
		}`;
	}

	async function handleTransactionCommit() {
		if (!transactionPreview) return;
		transactionCommitting = true;
		transactionError = null;
		try {
			await commitTransactionImportCsv(accountId, {
				new: transactionPreview.new,
				updated: transactionPreview.updated,
				omitted_ids: transactionPreview.omitted.map((t) => t.id)
			});
			transactionPreviewOpen = false;
			transactionPreview = null;
		} catch (err) {
			transactionError = err instanceof Error ? err.message : String(err);
		} finally {
			transactionCommitting = false;
		}
	}

	// ---------------------------------------------------------------------
	// Windfalls
	// ---------------------------------------------------------------------

	let windfallFileInput = $state<HTMLInputElement | undefined>();
	let windfallExporting = $state(false);
	let windfallPreviewLoading = $state(false);
	let windfallCommitting = $state(false);
	let windfallPreview = $state<WindfallImportPreview | null>(null);
	let windfallPreviewOpen = $state(false);
	let windfallParseErrors = $state<ImportRowIssue[] | null>(null);
	let windfallError = $state<string | null>(null);

	async function handleWindfallExport() {
		windfallExporting = true;
		windfallError = null;
		try {
			const blob = await exportWindfallsCsv(accountId);
			downloadBlob(blob, `windfalls-${accountId}.csv`);
		} catch (err) {
			windfallError = err instanceof Error ? err.message : String(err);
		} finally {
			windfallExporting = false;
		}
	}

	async function handleWindfallImportFile(event: Event) {
		const file = (event.target as HTMLInputElement).files?.[0];
		if (!file) return;
		windfallPreviewLoading = true;
		windfallError = null;
		windfallParseErrors = null;
		try {
			windfallPreview = await previewWindfallImportCsv(accountId, file);
			windfallPreviewOpen = true;
		} catch (err) {
			const errors = parseErrorsFrom(err);
			if (errors) {
				windfallParseErrors = errors;
			} else {
				windfallError = err instanceof Error ? err.message : String(err);
			}
		} finally {
			windfallPreviewLoading = false;
			if (windfallFileInput) windfallFileInput.value = '';
		}
	}

	function summarizeNewWindfall(fields: WindfallImportPreview['new'][number]): string {
		return `${fields.name} (${formatMoney(fields.amount_cents)}, expected ${fields.expected_date})`;
	}

	function summarizeUpdatedWindfall(update: WindfallImportPreview['updated'][number]): string {
		return `${update.fields.name} — ${update.fields.enabled ? 're-enabled' : 'disabled'}`;
	}

	function summarizeOmittedWindfall(windfall: Windfall): string {
		return `${windfall.name} (${formatMoney(windfall.amount_cents)}, expected ${windfall.expected_date})`;
	}

	async function handleWindfallCommit() {
		if (!windfallPreview) return;
		windfallCommitting = true;
		windfallError = null;
		try {
			await commitWindfallImportCsv(accountId, {
				new: windfallPreview.new,
				updated: windfallPreview.updated,
				omitted_ids: windfallPreview.omitted.map((w) => w.id)
			});
			windfallPreviewOpen = false;
			windfallPreview = null;
		} catch (err) {
			windfallError = err instanceof Error ? err.message : String(err);
		} finally {
			windfallCommitting = false;
		}
	}

	// ---------------------------------------------------------------------

	function downloadBlob(blob: Blob, filename: string) {
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = filename;
		link.click();
		URL.revokeObjectURL(url);
	}
</script>

<AccountNav {accountId} current="settings" />
<h1 class="mt-2 text-2xl font-semibold text-text">Settings{accountSuffix(account)}</h1>
<p class="mt-1 text-sm text-slate-500">
	Import and export CSVs for this account's bills, transactions, and windfalls. Re-importing an
	edited export reconciles against what's already here instead of duplicating it — see each
	section below for how matches, updates, and rows left off the file are handled.
</p>

<div class="mt-6 flex flex-col gap-6">
	<Card>
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold text-text">Bills</h2>
			<div class="flex gap-2">
				<input
					bind:this={billFileInput}
					type="file"
					accept=".csv,text/csv"
					class="hidden"
					onchange={handleBillImportFile}
				/>
				<Button
					variant="secondary"
					onclick={() => billFileInput?.click()}
					disabled={billPreviewLoading}
				>
					{billPreviewLoading ? 'Reading…' : 'Import CSV'}
				</Button>
				<Button variant="secondary" onclick={handleBillExport} disabled={billExporting}>
					{billExporting ? 'Exporting…' : 'Export CSV'}
				</Button>
			</div>
		</div>
		<p class="mt-2 text-sm text-slate-500">
			A bill matching an existing one (same name, amount, frequency, and start date) updates it in
			place. A bill left off the file gets disabled, not deleted — its history is kept.
		</p>
		{#if billError}
			<p class="mt-3 rounded-card bg-red-50 px-3 py-2 text-sm text-red-700">{billError}</p>
		{/if}
		{#if billParseErrors}
			<ul class="mt-3 rounded-card bg-red-50 px-3 py-2 text-sm text-red-700">
				{#each billParseErrors as rowError (rowError.row)}
					<li>Row {rowError.row}: {rowError.message}</li>
				{/each}
			</ul>
		{/if}
	</Card>

	<Card>
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold text-text">Transactions</h2>
			<div class="flex gap-2">
				<input
					bind:this={transactionFileInput}
					type="file"
					accept=".csv,text/csv"
					class="hidden"
					onchange={handleTransactionImportFile}
				/>
				<Button
					variant="secondary"
					onclick={() => transactionFileInput?.click()}
					disabled={transactionPreviewLoading}
				>
					{transactionPreviewLoading ? 'Reading…' : 'Import CSV'}
				</Button>
				<Button variant="secondary" onclick={handleTransactionExport} disabled={transactionExporting}>
					{transactionExporting ? 'Exporting…' : 'Export CSV'}
				</Button>
			</div>
		</div>
		<p class="mt-2 text-sm text-slate-500">
			Link a transaction to a bill with a <code>bill_name</code> column matching that bill's exact
			name. A transaction left off the file is permanently deleted — there's no history to preserve
			for transactions, so review the omitted list carefully before confirming.
		</p>
		{#if transactionError}
			<p class="mt-3 rounded-card bg-red-50 px-3 py-2 text-sm text-red-700">{transactionError}</p>
		{/if}
		{#if transactionParseErrors}
			<ul class="mt-3 rounded-card bg-red-50 px-3 py-2 text-sm text-red-700">
				{#each transactionParseErrors as rowError (rowError.row)}
					<li>Row {rowError.row}: {rowError.message}</li>
				{/each}
			</ul>
		{/if}
	</Card>

	<Card>
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold text-text">Windfalls</h2>
			<div class="flex gap-2">
				<input
					bind:this={windfallFileInput}
					type="file"
					accept=".csv,text/csv"
					class="hidden"
					onchange={handleWindfallImportFile}
				/>
				<Button
					variant="secondary"
					onclick={() => windfallFileInput?.click()}
					disabled={windfallPreviewLoading}
				>
					{windfallPreviewLoading ? 'Reading…' : 'Import CSV'}
				</Button>
				<Button variant="secondary" onclick={handleWindfallExport} disabled={windfallExporting}>
					{windfallExporting ? 'Exporting…' : 'Export CSV'}
				</Button>
			</div>
		</div>
		<p class="mt-2 text-sm text-slate-500">
			A windfall matching an existing one (same name, amount, and expected date) updates it in
			place. A windfall left off the file gets disabled, not deleted.
		</p>
		{#if windfallError}
			<p class="mt-3 rounded-card bg-red-50 px-3 py-2 text-sm text-red-700">{windfallError}</p>
		{/if}
		{#if windfallParseErrors}
			<ul class="mt-3 rounded-card bg-red-50 px-3 py-2 text-sm text-red-700">
				{#each windfallParseErrors as rowError (rowError.row)}
					<li>Row {rowError.row}: {rowError.message}</li>
				{/each}
			</ul>
		{/if}
	</Card>
</div>

{#if billPreview}
	<ImportPreviewModal
		bind:open={billPreviewOpen}
		title="Import bills"
		newSummaries={billPreview.new.map(summarizeNewBill)}
		updatedSummaries={billPreview.updated.map(summarizeUpdatedBill)}
		unchangedCount={billPreview.unchanged_count}
		ambiguousMessages={billPreview.ambiguous.map((a) => a.message)}
		omittedSummaries={billPreview.omitted.map(summarizeOmittedBill)}
		omittedSeverity="disable"
		confirming={billCommitting}
		onconfirm={handleBillCommit}
	/>
{/if}

{#if transactionPreview}
	<ImportPreviewModal
		bind:open={transactionPreviewOpen}
		title="Import transactions"
		newSummaries={transactionPreview.new.map(summarizeNewTransaction)}
		updatedSummaries={transactionPreview.updated.map(summarizeUpdatedTransaction)}
		unchangedCount={transactionPreview.unchanged_count}
		ambiguousMessages={transactionPreview.ambiguous.map((a) => a.message)}
		omittedSummaries={transactionPreview.omitted.map(summarizeOmittedTransaction)}
		omittedSeverity="delete"
		confirming={transactionCommitting}
		onconfirm={handleTransactionCommit}
	/>
{/if}

{#if windfallPreview}
	<ImportPreviewModal
		bind:open={windfallPreviewOpen}
		title="Import windfalls"
		newSummaries={windfallPreview.new.map(summarizeNewWindfall)}
		updatedSummaries={windfallPreview.updated.map(summarizeUpdatedWindfall)}
		unchangedCount={windfallPreview.unchanged_count}
		ambiguousMessages={windfallPreview.ambiguous.map((a) => a.message)}
		omittedSummaries={windfallPreview.omitted.map(summarizeOmittedWindfall)}
		omittedSeverity="disable"
		confirming={windfallCommitting}
		onconfirm={handleWindfallCommit}
	/>
{/if}
