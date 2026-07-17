<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Button from '$lib/components/Button.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import { initAuth, isAuthenticated, isLoading, login, logout, user } from '$lib/auth';
	import { onMount } from 'svelte';

	let { children } = $props();

	let mobileMenuOpen = $state(false);

	onMount(() => {
		initAuth();
	});

	function closeMobileMenu() {
		mobileMenuOpen = false;
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') closeMobileMenu();
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<svelte:window onkeydown={mobileMenuOpen ? handleKeydown : undefined} />

<div class="flex min-h-screen flex-col bg-background">
	<header class="border-b border-slate-200 bg-surface">
		<div class="flex items-center justify-between gap-3 px-4 py-4 sm:px-6">
			<div class="flex items-center gap-6">
				<a href="/" class="text-lg font-semibold text-primary">Tally</a>
				{#if $isAuthenticated}
					<nav class="hidden items-center gap-4 sm:flex" aria-label="Main">
						<a class="text-sm text-slate-600 hover:text-primary" href="/dashboard">Dashboard</a>
						<a class="text-sm text-slate-600 hover:text-primary" href="/accounts">Accounts</a>
						<a class="text-sm text-slate-600 hover:text-primary" href="/glossary">Glossary</a>
					</nav>
				{/if}
			</div>
			{#if $isLoading}
				<span class="text-sm text-slate-500">Loading...</span>
			{:else if $isAuthenticated}
				<div class="flex items-center gap-2 sm:gap-3">
					<span class="hidden text-sm text-slate-600 sm:inline">{$user?.email}</span>
					<span class="hidden sm:inline-flex">
						<Button variant="secondary" onclick={() => logout()}>Log out</Button>
					</span>
					<button
						type="button"
						class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-card text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-primary sm:hidden"
						aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
						aria-expanded={mobileMenuOpen}
						aria-controls="mobile-nav"
						onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
					>
						{#if mobileMenuOpen}
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								class="h-5 w-5"
							>
								<path d="M6 6l12 12M18 6L6 18" />
							</svg>
						{:else}
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								class="h-5 w-5"
							>
								<path d="M4 7h16M4 12h16M4 17h16" />
							</svg>
						{/if}
					</button>
				</div>
			{:else}
				<Button onclick={() => login()}>Log in</Button>
			{/if}
		</div>

		{#if $isAuthenticated && mobileMenuOpen}
			<nav
				id="mobile-nav"
				class="flex flex-col gap-1 border-t border-slate-200 px-4 py-3 sm:hidden"
				aria-label="Main"
			>
				<a
					class="rounded-card px-2 py-2 text-sm text-slate-600 hover:bg-slate-50 hover:text-primary"
					href="/dashboard"
					onclick={closeMobileMenu}
				>
					Dashboard
				</a>
				<a
					class="rounded-card px-2 py-2 text-sm text-slate-600 hover:bg-slate-50 hover:text-primary"
					href="/accounts"
					onclick={closeMobileMenu}
				>
					Accounts
				</a>
				<a
					class="rounded-card px-2 py-2 text-sm text-slate-600 hover:bg-slate-50 hover:text-primary"
					href="/glossary"
					onclick={closeMobileMenu}
				>
					Glossary
				</a>
				<div class="mt-1 flex items-center justify-between gap-2 border-t border-slate-100 px-2 pt-2">
					<span class="min-w-0 truncate text-xs text-slate-500">{$user?.email}</span>
					<Button
						variant="secondary"
						onclick={() => {
							closeMobileMenu();
							logout();
						}}
					>
						Log out
					</Button>
				</div>
			</nav>
		{/if}
	</header>

	<main class="mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-6">
		{@render children?.()}
	</main>

	<Footer />
</div>
