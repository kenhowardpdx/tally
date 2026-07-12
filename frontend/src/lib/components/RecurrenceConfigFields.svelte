<script lang="ts">
	import Input from '$lib/components/Input.svelte';
	import type { RecurrenceType } from '$lib/api/types';

	// Only semimonthly and custom_days need any recurrence_config at all -
	// see validate_recurrence_config (backend/src/forecast/bill.py), the
	// authoritative spec for these shapes. Every other type derives its
	// interval from start_date alone.
	let {
		recurrenceType,
		recurrenceConfig = $bindable({})
	}: {
		recurrenceType: RecurrenceType;
		recurrenceConfig: Record<string, unknown>;
	} = $props();

	const initialDays = Array.isArray(recurrenceConfig.days) ? recurrenceConfig.days : [10, 25];
	let day1 = $state(String(initialDays[0] ?? 10));
	let day2 = $state(String(initialDays[1] ?? 25));
	let intervalDays = $state(
		String(
			typeof recurrenceConfig.interval_days === 'number' ? recurrenceConfig.interval_days : 30
		)
	);

	// Only reads local $state (day1/day2/intervalDays) and recurrenceType, so
	// writing recurrenceConfig here doesn't re-trigger this same effect.
	$effect(() => {
		if (recurrenceType === 'semimonthly') {
			recurrenceConfig = { days: [Number(day1) || 10, Number(day2) || 25] };
		} else if (recurrenceType === 'custom_days') {
			recurrenceConfig = { interval_days: Number(intervalDays) || 30 };
		} else {
			recurrenceConfig = {};
		}
	});
</script>

{#if recurrenceType === 'semimonthly'}
	<Input label="Day 1 (1-31)" type="number" bind:value={day1} />
	<Input label="Day 2 (1-31)" type="number" bind:value={day2} />
{:else if recurrenceType === 'custom_days'}
	<Input label="Every N days" type="number" bind:value={intervalDays} />
{/if}
