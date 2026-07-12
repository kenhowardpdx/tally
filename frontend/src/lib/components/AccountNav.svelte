<script lang="ts">
	let {
		accountId,
		current
	}: {
		accountId: number;
		current: 'bills' | 'transactions' | 'windfalls' | 'forecast';
	} = $props();

	const links = $derived<{ key: typeof current; label: string; href: string }[]>([
		{ key: 'bills', label: 'Bills', href: `/accounts/${accountId}` },
		{ key: 'transactions', label: 'Transactions', href: `/accounts/${accountId}/transactions` },
		{ key: 'windfalls', label: 'Windfalls', href: `/accounts/${accountId}/windfalls` },
		{ key: 'forecast', label: 'Forecast', href: `/accounts/${accountId}/forecast` }
	]);
</script>

<div class="flex items-center justify-between">
	<a class="text-sm text-primary underline" href="/accounts">&larr; Accounts</a>
	<nav class="flex items-center gap-4">
		{#each links as link (link.key)}
			<a
				href={link.href}
				aria-current={link.key === current ? 'page' : undefined}
				class="text-sm {link.key === current
					? 'font-semibold text-primary'
					: 'text-slate-600 hover:text-primary'}"
			>
				{link.label}
			</a>
		{/each}
	</nav>
</div>
