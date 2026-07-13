<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import { glossaryTerms } from '$lib/glossary';
</script>

<h1 class="text-2xl font-semibold text-text">Glossary</h1>
<p class="mt-2 text-slate-600">
	Terms used throughout Tally that aren't self-explanatory from the UI alone.
</p>

<div class="mt-6 flex flex-col gap-4">
	{#each glossaryTerms as { term, definition } (term)}
		<Card>
			<h2 class="font-semibold text-text">{term}</h2>
			<p class="mt-1 text-sm text-slate-600">{definition}</p>
		</Card>
	{/each}
</div>
