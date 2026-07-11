<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
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

<header>
	{#if $isLoading}
		<span>Loading...</span>
	{:else if $isAuthenticated}
		<span>{$user?.email}</span>
		<button onclick={() => logout()}>Log out</button>
	{:else}
		<button onclick={() => login()}>Log in</button>
	{/if}
</header>

{@render children?.()}
