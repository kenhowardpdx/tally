<script lang="ts">
	import { Area, AreaChart, Circle, LinearGradient } from 'layerchart';
	import { curveMonotoneX } from 'd3-shape';
	import type { BalancePoint } from '$lib/forecast-chart';

	let { series }: { series: BalancePoint[] } = $props();

	const chartData = $derived(series.map((point) => ({ date: point.date, balance: point.balanceCents / 100 })));
	const lastPoint = $derived(chartData.at(-1));
	const endingBalanceCents = $derived(series.at(-1)?.balanceCents ?? 0);
	const endingDate = $derived(series.at(-1)?.date);
	const goesNegative = $derived(series.some((point) => point.balanceCents < 0));

	function formatAmount(cents: number): string {
		return (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
	}

	// Also used as the x-axis tick formatter (LayerChart passes it a Date
	// there) and the tooltip header formatter (passed the same field's raw
	// value, already a Date since chartData.date is one).
	function formatShortDate(value: unknown): string {
		const date = value instanceof Date ? value : new Date(value as string);
		return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
	}
</script>

{#if series.length > 1}
	<div class="rounded-card bg-surface p-6 shadow-card">
		<span
			class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {goesNegative
				? 'bg-red-100 text-red-800'
				: 'bg-emerald-100 text-emerald-800'}"
		>
			{goesNegative ? 'Negative forecast' : 'Positive forecast'}
		</span>
		<p class="mt-3 text-sm text-slate-600">
			{goesNegative
				? "We estimate your balance may dip below zero at some point in this period."
				: "We estimate you'll have a positive balance over this period."}
		</p>
		{#if endingDate}
			<p class="mt-4 text-3xl font-semibold {goesNegative ? 'text-red-700' : 'text-text'}">
				{formatAmount(endingBalanceCents)}
			</p>
			<p class="text-sm text-slate-500">{formatShortDate(endingDate)}</p>
		{/if}

		<div class="mt-4">
			<AreaChart
				data={chartData}
				x="date"
				y="balance"
				axis="x"
				series={[
					{ key: 'balance', value: 'balance', label: 'Balance', color: 'var(--color-primary)' }
				]}
				padding={{ left: 8, right: 8, top: 16, bottom: 24 }}
				height={220}
				props={{
					xAxis: { format: formatShortDate, ticks: 4 },
					tooltip: {
						header: { format: formatShortDate },
						item: { format: (value: number) => formatAmount(Math.round(value * 100)) }
					}
				}}
			>
				{#snippet marks({ context })}
					<LinearGradient class="from-primary/15 to-primary/0" vertical>
						{#snippet children({ gradient })}
							<Area
								curve={curveMonotoneX}
								line={{ class: 'stroke-primary stroke-2' }}
								fill={gradient}
							/>
						{/snippet}
					</LinearGradient>
					{#if lastPoint}
						<Circle
							cx={context.xGet(lastPoint)}
							cy={context.yGet(lastPoint)}
							r={5}
							class="fill-primary"
							stroke="var(--color-surface)"
							stroke-width={2}
						/>
					{/if}
				{/snippet}
			</AreaChart>
		</div>
	</div>
{/if}
