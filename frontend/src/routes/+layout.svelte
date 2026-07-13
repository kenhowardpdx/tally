<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Button from '$lib/components/Button.svelte';
	import { initAuth, isAuthenticated, isLoading, login, logout, user } from '$lib/auth';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		initAuth();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen bg-background">
	<header
		class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-surface px-4 py-4 sm:px-6"
	>
		<div class="flex flex-wrap items-center gap-4 sm:gap-6">
			<span class="text-lg font-semibold text-primary">Tally</span>
			{#if $isAuthenticated}
				<nav class="flex flex-wrap items-center gap-3 sm:gap-4">
					<a class="text-sm text-slate-600 hover:text-primary" href="/dashboard">Dashboard</a>
					<a class="text-sm text-slate-600 hover:text-primary" href="/accounts">Accounts</a>
					<a class="text-sm text-slate-600 hover:text-primary" href="/glossary">Glossary</a>
				</nav>
			{/if}
		</div>
		{#if $isLoading}
			<span class="text-sm text-slate-500">Loading...</span>
		{:else if $isAuthenticated}
			<div class="flex items-center gap-3">
				<span class="hidden text-sm text-slate-600 sm:inline">{$user?.email}</span>
				<Button variant="secondary" onclick={() => logout()}>Log out</Button>
			</div>
		{:else}
			<Button onclick={() => login()}>Log in</Button>
		{/if}
	</header>

	<main class="mx-auto max-w-4xl px-4 py-8 sm:px-6">
		{@render children?.()}
	</main>
</div>
