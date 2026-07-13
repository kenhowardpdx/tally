<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	const year = new Date().getFullYear();
</script>

<footer class="border-t border-slate-200 bg-surface">
	<div
		class="mx-auto flex max-w-4xl flex-col items-center justify-between gap-3 px-4 py-6 text-sm text-slate-500 sm:flex-row sm:px-6"
	>
		<div class="flex items-center gap-2">
			<img src={favicon} alt="" class="h-5 w-5" />
			<span>&copy; {year} Tally</span>
		</div>
		<nav class="flex items-center gap-4">
			<a href="/privacy" class="hover:text-primary">Privacy Policy</a>
			<a href="/terms" class="hover:text-primary">Terms and Conditions</a>
		</nav>
	</div>
</footer>
