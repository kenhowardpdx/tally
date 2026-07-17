import type { ForecastResponse } from '$lib/api/types';

export interface BalancePoint {
	date: Date;
	balanceCents: number;
}

// Local date components, not `new Date(iso)` (which parses as UTC midnight
// and can shift a day relative to the browser's local time zone) - matches
// the same local-date convention used elsewhere in this app (see
// format.ts's todayIso).
function parseLocalDate(iso: string): Date {
	const [year, month, day] = iso.split('-').map(Number);
	return new Date(year, month - 1, day);
}

// Turns the cycle-based forecast response into one balance point per cycle
// boundary (the starting anchor, then each cycle's end at its
// running_balance_cents). An earlier version plotted a point per bill/
// windfall/transaction event instead for more intra-cycle detail, but for
// short (weekly/biweekly) cycles over a long date range that produces a
// dense repeating sawtooth that reads as noise rather than a trend. Per-
// cycle points also use the backend's own running_balance_cents directly
// instead of re-deriving it client-side, so this can never drift from the
// cycle table above it.
export function buildBalanceSeries(forecast: ForecastResponse): BalancePoint[] {
	if (forecast.cycles.length === 0) return [];

	const points: BalancePoint[] = [
		{
			date: parseLocalDate(forecast.cycles[0].start_date),
			balanceCents: forecast.starting_balance_cents
		}
	];

	for (const cycle of forecast.cycles) {
		points.push({
			date: parseLocalDate(cycle.end_date),
			balanceCents: cycle.running_balance_cents
		});
	}

	return points;
}
