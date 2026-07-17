import { describe, expect, it } from 'vitest';
import { buildBalanceSeries } from '../forecast-chart';
import type { ForecastResponse } from '../api/types';

function cents(dollars: number): number {
	return Math.round(dollars * 100);
}

describe('buildBalanceSeries', () => {
	it('returns an empty series when there are no cycles', () => {
		const forecast: ForecastResponse = {
			cycles: [],
			starting_balance_cents: cents(100),
			ending_balance_cents: cents(100),
			unscheduled_bills: []
		};
		expect(buildBalanceSeries(forecast, 0)).toEqual([]);
	});

	it('anchors the first point at the first cycle start with the starting balance', () => {
		const forecast: ForecastResponse = {
			cycles: [
				{
					start_date: '2026-01-01',
					end_date: '2026-01-14',
					bills: [],
					transactions: [],
					windfalls: [],
					net_cents: 0,
					running_balance_cents: cents(500)
				}
			],
			starting_balance_cents: cents(500),
			ending_balance_cents: cents(500),
			unscheduled_bills: []
		};
		const series = buildBalanceSeries(forecast, 0);
		expect(series[0]).toEqual({ date: new Date(2026, 0, 1), balanceCents: cents(500) });
	});

	it('subtracts bills, adds windfalls and signed transactions, in date order', () => {
		const forecast: ForecastResponse = {
			cycles: [
				{
					start_date: '2026-01-01',
					end_date: '2026-01-14',
					bills: [
						{
							bill_id: 1,
							name: 'Rent',
							amount_cents: cents(100),
							forecasted_amount_cents: cents(100),
							due_date: '2026-01-05',
							completed: false,
							notes: null
						}
					],
					windfalls: [
						{
							windfall_id: 1,
							name: 'Bonus',
							amount_cents: cents(50),
							forecasted_amount_cents: cents(50),
							expected_date: '2026-01-03',
							completed: false,
							notes: null
						}
					],
					transactions: [
						{ transaction_id: 1, amount_cents: cents(-20), date: '2026-01-10', description: null }
					],
					net_cents: cents(50) + cents(-20) - cents(100),
					running_balance_cents: cents(500) + cents(50) + cents(-20) - cents(100)
				}
			],
			starting_balance_cents: cents(500),
			ending_balance_cents: cents(500) + cents(50) + cents(-20) - cents(100),
			unscheduled_bills: []
		};

		const series = buildBalanceSeries(forecast, 0);

		// start anchor, zero-income cycle-start event, windfall (1/3),
		// bill (1/5), transaction (1/10), cycle-end anchor (1/14)
		expect(series.map((p) => p.balanceCents)).toEqual([
			cents(500), // start anchor
			cents(500), // cycle-start income event (0 in this test)
			cents(550), // + windfall 50
			cents(450), // - bill 100
			cents(430), // + transaction -20
			cents(430) // cycle end, unchanged
		]);
		expect(series.at(-1)!.date).toEqual(new Date(2026, 0, 14));
	});

	it('uses amount_cents (override-applied), not forecasted_amount_cents', () => {
		const forecast: ForecastResponse = {
			cycles: [
				{
					start_date: '2026-01-01',
					end_date: '2026-01-14',
					bills: [
						{
							bill_id: 1,
							name: 'Utilities',
							amount_cents: cents(75), // overridden actual
							forecasted_amount_cents: cents(100), // original estimate
							due_date: '2026-01-05',
							completed: true,
							notes: null
						}
					],
					transactions: [],
					windfalls: [],
					net_cents: cents(-75),
					running_balance_cents: cents(500) - cents(75)
				}
			],
			starting_balance_cents: cents(500),
			ending_balance_cents: cents(500) - cents(75),
			unscheduled_bills: []
		};

		const series = buildBalanceSeries(forecast, 0);
		expect(series.map((p) => p.balanceCents)).toEqual([
			cents(500), // start anchor
			cents(500), // cycle-start income event (0 in this test)
			cents(425), // - overridden bill amount (75), not the forecasted 100
			cents(425) // cycle end, unchanged
		]);
	});

	it('anchors income_per_cycle_cents at each cycle start', () => {
		const forecast: ForecastResponse = {
			cycles: [
				{
					start_date: '2026-01-01',
					end_date: '2026-01-14',
					bills: [],
					transactions: [],
					windfalls: [],
					net_cents: 0,
					running_balance_cents: cents(600)
				},
				{
					start_date: '2026-01-15',
					end_date: '2026-01-28',
					bills: [],
					transactions: [],
					windfalls: [],
					net_cents: 0,
					running_balance_cents: cents(700)
				}
			],
			starting_balance_cents: cents(500),
			ending_balance_cents: cents(700),
			unscheduled_bills: []
		};

		const series = buildBalanceSeries(forecast, cents(100));
		expect(series.map((p) => p.balanceCents)).toEqual([
			cents(500), // start anchor
			cents(600), // + income at cycle 1 start
			cents(600), // cycle 1 end anchor
			cents(700), // + income at cycle 2 start
			cents(700) // cycle 2 end anchor
		]);
	});
});
