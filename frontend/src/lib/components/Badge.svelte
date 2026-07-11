<script lang="ts">
	let { enabled }: { enabled: boolean } = $props();
</script>

{#if enabled}
	<span
		class="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800"
	>
		Enabled
	</span>
{:else}
	<span
		class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600"
	>
		Disabled
	</span>
{/if}
