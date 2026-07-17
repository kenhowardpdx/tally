import { describe, expect, it } from 'vitest';
import { buildBalanceSeries } from '../forecast-chart';
import type { ForecastCycle, ForecastResponse } from '../api/types';

function cents(dollars: number): number {
	return Math.round(dollars * 100);
}

function emptyCycle(overrides: Partial<ForecastCycle>): ForecastCycle {
	return {
		start_date: '2026-01-01',
		end_date: '2026-01-14',
		bills: [],
		transactions: [],
		windfalls: [],
		net_cents: 0,
		running_balance_cents: 0,
		...overrides
	};
}

describe('buildBalanceSeries', () => {
	it('returns an empty series when there are no cycles', () => {
		const forecast: ForecastResponse = {
			cycles: [],
			starting_balance_cents: cents(100),
			ending_balance_cents: cents(100),
			unscheduled_bills: []
		};
		expect(buildBalanceSeries(forecast)).toEqual([]);
	});

	it('anchors the first point at the first cycle start with the starting balance', () => {
		const forecast: ForecastResponse = {
			cycles: [emptyCycle({ running_balance_cents: cents(500) })],
			starting_balance_cents: cents(500),
			ending_balance_cents: cents(500),
			unscheduled_bills: []
		};
		const series = buildBalanceSeries(forecast);
		expect(series[0]).toEqual({ date: new Date(2026, 0, 1), balanceCents: cents(500) });
	});

	it('emits exactly one point per cycle end, using running_balance_cents directly', () => {
		// A cycle's bills/transactions/windfalls don't matter here - the chart
		// no longer re-derives the balance from them (that's the whole point:
		// it trusts the backend's own running_balance_cents so it can never
		// drift from the cycle table), so this only needs to be internally
		// consistent, not arithmetically verified against net_cents.
		const forecast: ForecastResponse = {
			cycles: [
				emptyCycle({
					start_date: '2026-01-01',
					end_date: '2026-01-14',
					running_balance_cents: cents(650)
				}),
				emptyCycle({
					start_date: '2026-01-15',
					end_date: '2026-01-28',
					running_balance_cents: cents(430)
				})
			],
			starting_balance_cents: cents(500),
			ending_balance_cents: cents(430),
			unscheduled_bills: []
		};

		const series = buildBalanceSeries(forecast);

		expect(series).toEqual([
			{ date: new Date(2026, 0, 1), balanceCents: cents(500) }, // start anchor
			{ date: new Date(2026, 0, 14), balanceCents: cents(650) }, // cycle 1 end
			{ date: new Date(2026, 0, 28), balanceCents: cents(430) } // cycle 2 end
		]);
	});
});
