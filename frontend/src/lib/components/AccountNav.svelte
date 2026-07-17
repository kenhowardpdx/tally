<script lang="ts">
	let {
		accountId,
		current
	}: {
		accountId: number;
		current: 'bills' | 'transactions' | 'windfalls' | 'forecast' | 'settings';
	} = $props();

	const links = $derived<{ key: typeof current; label: string; href: string }[]>([
		{ key: 'bills', label: 'Bills', href: `/accounts/${accountId}` },
		{ key: 'transactions', label: 'Transactions', href: `/accounts/${accountId}/transactions` },
		{ key: 'windfalls', label: 'Windfalls', href: `/accounts/${accountId}/windfalls` },
		{ key: 'forecast', label: 'Forecast', href: `/accounts/${accountId}/forecast` },
		{ key: 'settings', label: 'Settings', href: `/accounts/${accountId}/settings` }
	]);

	let scrollEl = $state<HTMLElement | undefined>();
	let showLeftFade = $state(false);
	let showRightFade = $state(false);

	// Narrow viewports can't fit all five links - the nav scrolls
	// horizontally instead, and these fades are the visual affordance that
	// there's more to scroll to.
	function updateFades() {
		if (!scrollEl) return;
		showLeftFade = scrollEl.scrollLeft > 4;
		showRightFade = scrollEl.scrollLeft + scrollEl.clientWidth < scrollEl.scrollWidth - 4;
	}

	$effect(() => {
		if (scrollEl) updateFades();
	});
</script>

<svelte:window onresize={updateFades} />

<div class="flex items-center gap-3">
	<a class="shrink-0 text-sm text-primary underline" href="/accounts">&larr; Accounts</a>
	<div class="relative min-w-0 flex-1">
		<nav
			bind:this={scrollEl}
			onscroll={updateFades}
			class="flex items-center gap-4 overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
			aria-label="Account"
		>
			{#each links as link (link.key)}
				<a
					href={link.href}
					aria-current={link.key === current ? 'page' : undefined}
					class="shrink-0 whitespace-nowrap text-sm {link.key === current
						? 'font-semibold text-primary'
						: 'text-slate-600 hover:text-primary'}"
				>
					{link.label}
				</a>
			{/each}
		</nav>
		{#if showLeftFade}
			<div
				class="pointer-events-none absolute inset-y-0 left-0 flex w-8 items-center justify-start bg-gradient-to-r from-background to-transparent"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2.5"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="h-3 w-3 text-slate-400"
				>
					<path d="M15 6l-6 6 6 6" />
				</svg>
			</div>
		{/if}
		{#if showRightFade}
			<div
				class="pointer-events-none absolute inset-y-0 right-0 flex w-8 items-center justify-end bg-gradient-to-l from-background to-transparent"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2.5"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="h-3 w-3 text-slate-400"
				>
					<path d="M9 6l6 6-6 6" />
				</svg>
			</div>
		{/if}
	</div>
</div>
