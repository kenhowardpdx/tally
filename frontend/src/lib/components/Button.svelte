<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'primary' | 'secondary' | 'danger';

	let {
		variant = 'primary',
		type = 'button',
		disabled = false,
		onclick,
		children
	}: {
		variant?: Variant;
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		onclick?: (event: MouseEvent) => void;
		children: Snippet;
	} = $props();

	const variantClasses: Record<Variant, string> = {
		primary: 'bg-primary text-white hover:bg-primary/90',
		secondary: 'bg-surface text-text border border-slate-300 hover:bg-slate-50',
		danger: 'bg-red-600 text-white hover:bg-red-700'
	};
</script>

<button
	{type}
	{disabled}
	{onclick}
	class="rounded-card px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 {variantClasses[
		variant
	]}"
>
	{@render children()}
</button>
