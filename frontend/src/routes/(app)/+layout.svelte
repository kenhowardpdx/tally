<script lang="ts">
	import { acceptConsent, getConsentStatus } from '$lib/api/consent';
	import Button from '$lib/components/Button.svelte';
	import Card from '$lib/components/Card.svelte';
	import { isAuthenticated, isLoading, login } from '$lib/auth';

	let { children } = $props();

	let consentLoading = $state(true);
	let consentAccepted = $state(false);
	let accepting = $state(false);
	let error = $state<string | null>(null);

	// Every route under this group requires auth: while loading, render
	// nothing meaningful; once resolved, redirect unauthenticated visitors to
	// Auth0 login instead of rendering the page.
	$effect(() => {
		if (!$isLoading && !$isAuthenticated) login();
	});

	// Consent is tracked in our own backend rather than as an Auth0 signup
	// checkbox (see docs/ROADMAP.md) - gate here so it's checked once per
	// session right after auth resolves, for every route in this group.
	$effect(() => {
		if ($isAuthenticated) checkConsent();
	});

	async function checkConsent() {
		consentLoading = true;
		error = null;
		try {
			const status = await getConsentStatus();
			consentAccepted = status.terms_accepted;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			consentLoading = false;
		}
	}

	async function handleAccept() {
		accepting = true;
		error = null;
		try {
			await acceptConsent();
			consentAccepted = true;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			accepting = false;
		}
	}
</script>

{#if $isLoading || ($isAuthenticated && consentLoading)}
	<p class="text-sm text-slate-500">Loading...</p>
{:else if $isAuthenticated && !consentAccepted}
	<Card>
		<h1 class="text-xl font-semibold text-text">Before you continue</h1>
		<p class="mt-2 text-sm text-slate-600">
			Please review and accept our
			<a class="text-primary underline" href="/privacy">Privacy Policy</a>
			and <a class="text-primary underline" href="/terms">Terms and Conditions</a> to continue
			using Tally.
		</p>
		{#if error}
			<p class="mt-4 rounded-card bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
		{/if}
		<div class="mt-4">
			<Button onclick={handleAccept} disabled={accepting}>
				{accepting ? 'Saving...' : 'I agree - continue'}
			</Button>
		</div>
	</Card>
{:else if $isAuthenticated}
	{@render children?.()}
{/if}
