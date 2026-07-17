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

// Turns the cycle-based forecast response into a point-per-event balance
// series, instead of one point per cycle boundary - walks every bill/
// windfall/transaction date within each cycle so the chart's line moves on
// the date something actually happens, not just at cycle edges.
//
// Uses each line's `amount_cents` (override-applied actual), matching what
// the backend's own net_cents/running_balance_cents are computed from (see
// build_cycle in backend/src/forecast/cycle.py) - forecasted_amount_cents
// would silently diverge from the balances shown in the cycle table
// whenever an override is set.
//
// income_per_cycle_cents isn't tied to a specific date in the response (it's
// a flat per-cycle assumption, not a scheduled line item), so it's anchored
// at each cycle's start_date - a paycheck-at-the-start-of-the-pay-period is
// the most natural reading of what "income per cycle" represents.
export function buildBalanceSeries(
	forecast: ForecastResponse,
	incomePerCycleCents: number
): BalancePoint[] {
	if (forecast.cycles.length === 0) return [];

	const points: BalancePoint[] = [
		{
			date: parseLocalDate(forecast.cycles[0].start_date),
			balanceCents: forecast.starting_balance_cents
		}
	];

	let running = forecast.starting_balance_cents;
	for (const cycle of forecast.cycles) {
		const events = [
			...cycle.bills.map((line) => ({ date: line.due_date, amountCents: -line.amount_cents })),
			...cycle.windfalls.map((line) => ({
				date: line.expected_date,
				amountCents: line.amount_cents
			})),
			...cycle.transactions.map((line) => ({ date: line.date, amountCents: line.amount_cents })),
			{ date: cycle.start_date, amountCents: incomePerCycleCents }
		].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

		for (const event of events) {
			running += event.amountCents;
			points.push({ date: parseLocalDate(event.date), balanceCents: running });
		}

		// Anchors the cycle's end even when nothing happened on that exact
		// date, so a quiet cycle still reads as a flat segment rather than a
		// gap in the line.
		points.push({ date: parseLocalDate(cycle.end_date), balanceCents: running });
	}

	return points;
}
