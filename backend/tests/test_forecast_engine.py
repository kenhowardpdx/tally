"""Pure unit tests for src/forecast - no DB, no HTTP.

The bi-weekly and monthly golden values below are ported directly from the
reference TypeScript engine's test suites (kenhowardpdx/bank,
packages/forecast/src/__tests__/{cycle,forecast}.test.ts), converted from
dollar strings to cents and adapted to Tally's positive-amount convention
(Bill.amount_cents is stored positive; the reference stores bill amounts
pre-negated). All bills in the reference fixtures omit `type`, which the
reference's Bill class treats as falsy-not-"annually" - i.e. they behave as
monthly bills, ported here as RecurrenceType.MONTHLY.

The semimonthly (10th/25th) golden values are NOT ported as-is: the
reference's day-bucket boundary for snapping an arbitrary start date onto the
10th/25th anchor is itself buggy (day 21 snaps to the 25th, skipping the
still-in-progress 10th-24th period entirely) and is exactly the
`start`/`next` object-aliasing code this port intentionally rewrites rather
than reproduces. This port goes further than just fixing the bucket
boundary, though: it doesn't snap the *first* cycle's start backward onto a
10th/25th anchor at all (see _cycle_bounds in engine.py) - doing so would
silently include bills from before the caller's actual start_date in the
first cycle, corrupting the meaning of starting_balance_cents (a real bug
caught in PR review). The first semimonthly cycle can end up shorter than a
full half-month as a result; every cycle after that is a full period. The
semimonthly cases below pin this engine's own (verified self-consistent)
output instead.
"""

from datetime import date

import pytest

from src.forecast import (
    ForecastBill,
    ForecastTransaction,
    ForecastWindfall,
    MissingRecurrenceConfig,
    build_cycle,
    get_forecast,
    last_cycle_end,
)
from src.forecast.bill import occurrences_in_range, validate_recurrence_config
from src.models.bank_account import CycleType
from src.models.bill import RecurrenceType


def make_bill(
    id: int,
    name: str,
    amount_cents: int,
    start_date: date,
    end_date: date | None = None,
    recurrence_type: RecurrenceType = RecurrenceType.MONTHLY,
    recurrence_config: dict | None = None,
) -> ForecastBill:
    return ForecastBill(
        id=id,
        name=name,
        amount_cents=amount_cents,
        recurrence_type=recurrence_type,
        recurrence_config=recurrence_config or {},
        start_date=start_date,
        end_date=end_date,
    )


class TestGetForecastBiWeeklyGoldenValues:
    def test_no_bills_single_cycle(self):
        result = get_forecast([], CycleType.BIWEEKLY, date(1985, 10, 21), date(1985, 10, 28), 2498, 15999)
        assert len(result.cycles) == 1
        assert result.ending_balance_cents == 18497

    def test_no_bills_multiple_cycles(self):
        result = get_forecast([], CycleType.BIWEEKLY, date(1985, 10, 21), date(1985, 11, 28), 2498, 15999)
        assert len(result.cycles) == 3
        assert result.ending_balance_cents == 50495

    def test_two_bills(self):
        bills = [
            make_bill(1, "foo", 10000, date(1985, 10, 11)),
            make_bill(2, "bar", 1985, date(1985, 1, 18)),
        ]
        result = get_forecast(bills, CycleType.BIWEEKLY, date(1985, 10, 21), date(1985, 11, 28), 2498, 15999)
        assert len(result.cycles) == 3
        assert result.ending_balance_cents == 38510

    def test_two_bills_one_large_goes_negative(self):
        bills = [
            make_bill(1, "foo", 10000, date(1985, 10, 11)),
            make_bill(2, "bar", 271985, date(1985, 1, 18)),
        ]
        result = get_forecast(bills, CycleType.BIWEEKLY, date(1985, 10, 21), date(1985, 11, 28), 2498, 15999)
        assert len(result.cycles) == 3
        assert result.ending_balance_cents == -231490


class TestGetForecastMonthlyGoldenValues:
    def test_no_bills_single_cycle(self):
        result = get_forecast([], CycleType.MONTHLY, date(1985, 10, 21), date(1985, 10, 28), 2498, 15999)
        assert len(result.cycles) == 1
        assert result.ending_balance_cents == 18497

    def test_no_bills_multiple_cycles(self):
        result = get_forecast([], CycleType.MONTHLY, date(1985, 10, 21), date(1986, 1, 22), 2498, 15999)
        assert len(result.cycles) == 4
        assert result.ending_balance_cents == 66494

    def test_two_bills(self):
        bills = [
            make_bill(1, "foo", 10000, date(1985, 10, 11)),
            make_bill(2, "bar", 1985, date(1985, 1, 18)),
        ]
        result = get_forecast(bills, CycleType.MONTHLY, date(1985, 10, 21), date(1986, 1, 20), 2498, 15999)
        assert len(result.cycles) == 3
        assert result.ending_balance_cents == 14540

    def test_two_bills_one_large_goes_negative(self):
        bills = [
            make_bill(1, "foo", 10000, date(1985, 10, 11)),
            make_bill(2, "bar", 271985, date(1985, 1, 18)),
        ]
        result = get_forecast(bills, CycleType.MONTHLY, date(1985, 10, 21), date(1985, 11, 28), 2498, 15999)
        assert len(result.cycles) == 2
        assert result.ending_balance_cents == -529474


class TestGetForecastSemimonthly:
    """See module docstring - these pin this engine's own corrected output,
    not the reference's (buggy) day-bucket snapping."""

    def test_no_bills(self):
        result = get_forecast([], CycleType.SEMIMONTHLY, date(1985, 10, 21), date(1985, 12, 28), 2498, 15999)
        assert len(result.cycles) == 6
        assert result.ending_balance_cents == 98492

    def test_two_bills_one_large_goes_negative(self):
        bills = [
            make_bill(1, "foo", 10000, date(1985, 10, 11)),
            make_bill(2, "bar", 271985, date(1985, 1, 18)),
        ]
        result = get_forecast(bills, CycleType.SEMIMONTHLY, date(1985, 10, 21), date(1985, 11, 28), 2498, 15999)
        assert len(result.cycles) == 4
        assert result.ending_balance_cents == -215491

    def test_first_cycle_honors_exact_start_date_not_the_10th_25th_anchor(self):
        # A mid-period start_date (the 21st) must not be snapped backward to
        # the 10th - that would silently pull bills due the 10th-20th into
        # the first cycle even though starting_balance_cents is supposed to
        # represent the balance as of the 21st, not the 10th.
        bill = make_bill(1, "already happened", 5000, date(2024, 1, 15))
        result = get_forecast(
            [bill], CycleType.SEMIMONTHLY, date(2024, 1, 21), date(2024, 1, 21), 0, 0
        )
        assert result.cycles[0].start_date == date(2024, 1, 21)
        assert result.cycles[0].end_date == date(2024, 1, 24)
        assert result.cycles[0].bills == []
        assert result.ending_balance_cents == 0


class TestGetForecastWeekly:
    """No reference fixture exists for this - the reference's engine leaves
    weekly unimplemented ("NOT IMPLEMENTED"). Hand-verified."""

    def test_no_bills(self):
        result = get_forecast([], CycleType.WEEKLY, date(2024, 1, 1), date(2024, 1, 21), 0, 1000)
        # 3 flush 7-day windows: 1/1-1/7, 1/8-1/14, 1/15-1/21
        assert len(result.cycles) == 3
        assert result.ending_balance_cents == 3000

    def test_weekly_bill_recurs_multiple_times_within_a_monthly_cycle(self):
        """A weekly-recurring bill inside a longer (monthly) cycle window can
        genuinely recur more than once - the reference's single-occurrence-
        per-cycle model can't represent this; this port generalizes it."""
        bill = make_bill(1, "coffee", 500, date(2024, 1, 3), recurrence_type=RecurrenceType.WEEKLY)
        result = get_forecast([bill], CycleType.MONTHLY, date(2024, 1, 1), date(2024, 1, 31), 0, 0)
        assert len(result.cycles) == 1
        # Jan 3, 10, 17, 24, 31 - five occurrences within the one monthly cycle.
        assert len(result.cycles[0].bills) == 5
        assert result.ending_balance_cents == -2500


class TestCycleGoldenValue:
    """Ports cycle.test.ts's "multiple cycles" fixture - one terminated bill
    plus two open-ended ones, evaluated a month apart."""

    def test_bill_with_end_date_drops_out_of_later_cycle(self):
        bills = [
            make_bill(1, "bill one", 1525, date(1985, 10, 22), end_date=date(1985, 10, 22)),
            make_bill(2, "bill two", 1525, date(1985, 10, 22)),
            make_bill(3, "bill three", 1525, date(1985, 10, 23)),
        ]
        cycle_one = build_cycle(bills, [], [], date(1985, 10, 21), date(1985, 10, 28))
        cycle_two = build_cycle(bills, [], [], date(1985, 11, 21), date(1985, 11, 28))

        assert len(cycle_one.bills) != len(cycle_two.bills)
        # net_cents is negative for bills-only cycles (bills are expenses,
        # subtracted) - the reference's golden value (-76.25, its bills are
        # stored pre-negated) matches this sign directly, unlike the other
        # ported fixtures which had to flip sign for Tally's positive-amount
        # convention.
        assert cycle_one.net_cents + cycle_two.net_cents == -7625


class TestDueDateMonthEndClamping:
    def test_bill_anchored_on_31st_clamps_in_february(self):
        bill = make_bill(1, "rent", 100000, date(2023, 1, 31))
        occurrences = occurrences_in_range(bill, date(2024, 2, 1), date(2024, 2, 29))
        assert occurrences == [date(2024, 2, 29)]

    def test_bill_anchored_on_31st_clamps_in_non_leap_february(self):
        bill = make_bill(1, "rent", 100000, date(2023, 1, 31))
        occurrences = occurrences_in_range(bill, date(2023, 2, 1), date(2023, 2, 28))
        assert occurrences == [date(2023, 2, 28)]


class TestRecurrenceConfigValidation:
    def test_semimonthly_with_config(self):
        bill = make_bill(
            1, "rent", 50000, date(2024, 1, 1),
            recurrence_type=RecurrenceType.SEMIMONTHLY,
            recurrence_config={"days": [10, 25]},
        )
        assert validate_recurrence_config(bill) is None
        occurrences = occurrences_in_range(bill, date(2024, 3, 1), date(2024, 3, 31))
        assert occurrences == [date(2024, 3, 10), date(2024, 3, 25)]

    def test_semimonthly_missing_config_raises(self):
        bill = make_bill(1, "rent", 50000, date(2024, 1, 1), recurrence_type=RecurrenceType.SEMIMONTHLY)
        assert validate_recurrence_config(bill) is not None

    @pytest.mark.parametrize("days", [[0, 25], [10, 32], [-5, 10]])
    def test_semimonthly_out_of_range_days_raises_instead_of_crashing(self, days):
        # date(year, month, day) raises ValueError for day outside 1-31 - out
        # of range recurrence_config.days must be treated as missing config
        # (skip + reason), not reach date() construction and 500 the request.
        bill = make_bill(
            1, "rent", 50000, date(2024, 1, 1),
            recurrence_type=RecurrenceType.SEMIMONTHLY,
            recurrence_config={"days": days},
        )
        assert validate_recurrence_config(bill) is not None
        with pytest.raises(MissingRecurrenceConfig):
            occurrences_in_range(bill, date(2024, 3, 1), date(2024, 3, 31))

    def test_custom_days_with_config(self):
        bill = make_bill(
            1, "trash", 2000, date(2024, 1, 1),
            recurrence_type=RecurrenceType.CUSTOM_DAYS,
            recurrence_config={"interval_days": 45},
        )
        occurrences = occurrences_in_range(bill, date(2024, 2, 1), date(2024, 2, 29))
        assert occurrences == [date(2024, 2, 15)]

    def test_custom_days_missing_config_raises(self):
        bill = make_bill(1, "trash", 2000, date(2024, 1, 1), recurrence_type=RecurrenceType.CUSTOM_DAYS)
        with pytest.raises(MissingRecurrenceConfig):
            occurrences_in_range(bill, date(2024, 2, 1), date(2024, 2, 29))

    def test_get_forecast_skips_unconfigured_bills_instead_of_failing(self):
        good_bill = make_bill(1, "rent", 50000, date(2024, 1, 1))
        bad_bill = make_bill(
            2, "irregular", 2000, date(2024, 1, 1), recurrence_type=RecurrenceType.CUSTOM_DAYS
        )
        result = get_forecast(
            [good_bill, bad_bill], CycleType.MONTHLY, date(2024, 1, 1), date(2024, 1, 31), 0, 0
        )
        assert len(result.unscheduled_bills) == 1
        assert result.unscheduled_bills[0].bill_id == 2
        # good_bill still gets forecast normally despite bad_bill's problem.
        assert len(result.cycles[0].bills) == 1
        assert result.cycles[0].bills[0].bill_id == 1


class TestGetForecastValidation:
    def test_end_date_before_start_date_raises(self):
        with pytest.raises(ValueError):
            get_forecast([], CycleType.MONTHLY, date(2024, 2, 1), date(2024, 1, 1), 0, 0)

    def test_single_day_range_still_produces_one_cycle(self):
        # Deliberate improvement over the reference, which produces zero
        # cycles when end_date == start_date (an untested degenerate case
        # there) - a forecast for a single day should still show that day.
        result = get_forecast([], CycleType.MONTHLY, date(2024, 1, 1), date(2024, 1, 1), 0, 0)
        assert len(result.cycles) == 1


class TestLastCycleEnd:
    def test_matches_final_cycle_end_date_from_get_forecast(self):
        # Weekly cycles are 7 days - a 10-day window's last cycle necessarily
        # runs past end_date, which is exactly the case last_cycle_end exists
        # to compute correctly for query-bounding callers.
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)
        result = get_forecast([], CycleType.WEEKLY, start, end, 0, 0)
        assert last_cycle_end(CycleType.WEEKLY, start, end) == result.cycles[-1].end_date
        assert result.cycles[-1].end_date > end

    def test_end_date_before_start_date_raises(self):
        with pytest.raises(ValueError):
            last_cycle_end(CycleType.MONTHLY, date(2024, 2, 1), date(2024, 1, 1))


class TestGetForecastTransactionsAndWindfalls:
    def test_windfall_adds_to_running_balance(self):
        windfall = ForecastWindfall(id=1, name="tax refund", amount_cents=50000, expected_date=date(2024, 1, 15))
        result = get_forecast(
            [], CycleType.MONTHLY, date(2024, 1, 1), date(2024, 1, 31), 0, 0, windfalls=[windfall]
        )
        assert len(result.cycles[0].windfalls) == 1
        assert result.cycles[0].net_cents == 50000
        assert result.ending_balance_cents == 50000

    def test_positive_transaction_credits_negative_transaction_debits(self):
        credit = ForecastTransaction(id=1, amount_cents=10000, date=date(2024, 1, 5), description="refund")
        debit = ForecastTransaction(id=2, amount_cents=-3000, date=date(2024, 1, 10), description="oops")
        result = get_forecast(
            [], CycleType.MONTHLY, date(2024, 1, 1), date(2024, 1, 31), 0, 0, transactions=[credit, debit]
        )
        assert len(result.cycles[0].transactions) == 2
        assert result.cycles[0].net_cents == 7000
        assert result.ending_balance_cents == 7000

    def test_bills_transactions_and_windfalls_combine_in_one_cycle(self):
        bill = make_bill(1, "rent", 150000, date(2024, 1, 1))
        transaction = ForecastTransaction(id=1, amount_cents=-2000, date=date(2024, 1, 10), description=None)
        windfall = ForecastWindfall(id=1, name="bonus", amount_cents=100000, expected_date=date(2024, 1, 20))
        result = get_forecast(
            [bill],
            CycleType.MONTHLY,
            date(2024, 1, 1),
            date(2024, 1, 31),
            0,
            0,
            transactions=[transaction],
            windfalls=[windfall],
        )
        # -150000 (bill) - 2000 (transaction) + 100000 (windfall)
        assert result.cycles[0].net_cents == -52000
        assert result.ending_balance_cents == -52000

    def test_transaction_and_windfall_outside_cycle_window_excluded(self):
        transaction = ForecastTransaction(id=1, amount_cents=10000, date=date(2024, 2, 1), description=None)
        windfall = ForecastWindfall(id=1, name="late", amount_cents=5000, expected_date=date(2024, 2, 1))
        result = get_forecast(
            [],
            CycleType.MONTHLY,
            date(2024, 1, 1),
            date(2024, 1, 31),
            0,
            0,
            transactions=[transaction],
            windfalls=[windfall],
        )
        assert result.cycles[0].transactions == []
        assert result.cycles[0].windfalls == []
        assert result.cycles[0].net_cents == 0
