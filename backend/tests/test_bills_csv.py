from datetime import date

from src.bills_csv import CSV_COLUMNS, bills_to_csv, parse_csv_rows
from src.models.bill import Bill, RecurrenceType


def _bill(**overrides) -> Bill:
    defaults = dict(
        id=1,
        account_id=1,
        name="Rent",
        amount_cents=150000,
        recurrence_type=RecurrenceType.MONTHLY,
        recurrence_config={},
        start_date=date(2026, 1, 1),
        end_date=None,
        enabled=True,
        notes=None,
    )
    defaults.update(overrides)
    return Bill(**defaults)


class TestBillsToCsv:
    def test_round_trips_basic_fields(self):
        csv_text = bills_to_csv([_bill(notes="fixed rate")])
        bills, errors = parse_csv_rows(csv_text)

        assert errors == []
        assert len(bills) == 1
        assert bills[0].name == "Rent"
        assert bills[0].amount_cents == 150000
        assert bills[0].notes == "fixed rate"

    def test_semimonthly_days_flattened_into_own_column(self):
        bill = _bill(
            recurrence_type=RecurrenceType.SEMIMONTHLY, recurrence_config={"days": [10, 25]}
        )
        csv_text = bills_to_csv([bill])

        assert "10,25" in csv_text
        bills, errors = parse_csv_rows(csv_text)
        assert errors == []
        assert bills[0].recurrence_config == {"days": [10, 25]}

    def test_custom_days_interval_flattened_into_own_column(self):
        bill = _bill(
            recurrence_type=RecurrenceType.CUSTOM_DAYS, recurrence_config={"interval_days": 45}
        )
        csv_text = bills_to_csv([bill])

        bills, errors = parse_csv_rows(csv_text)
        assert errors == []
        assert bills[0].recurrence_config == {"interval_days": 45}

    def test_header_matches_csv_columns_constant(self):
        csv_text = bills_to_csv([])
        header = csv_text.splitlines()[0]
        assert header == ",".join(CSV_COLUMNS)


class TestParseCsvRows:
    def test_missing_required_field_reports_row_number(self):
        csv_text = (
            "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
            "start_date,end_date,enabled,notes\n"
            ",100.00,monthly,,,2026-01-01,,true,\n"
        )
        bills, errors = parse_csv_rows(csv_text)

        assert bills == []
        assert len(errors) == 1
        assert errors[0].row == 2
        assert "name" in errors[0].message

    def test_invalid_recurrence_type_reports_error(self):
        csv_text = (
            "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
            "start_date,end_date,enabled,notes\n"
            "Rent,100.00,bogus,,,2026-01-01,,true,\n"
        )
        bills, errors = parse_csv_rows(csv_text)

        assert bills == []
        assert len(errors) == 1
        assert "recurrence_type" in errors[0].message

    def test_semimonthly_without_days_reports_error(self):
        csv_text = (
            "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
            "start_date,end_date,enabled,notes\n"
            "Rent,100.00,semimonthly,,,2026-01-01,,true,\n"
        )
        bills, errors = parse_csv_rows(csv_text)

        assert bills == []
        assert len(errors) == 1
        # Message now comes from the shared validate_recurrence_config
        # (backend/src/forecast/bill.py), the same one the JSON create/update
        # API path uses - "recurrence_config.days" rather than the CSV
        # column name, but consistent across both paths.
        assert "days" in errors[0].message

    def test_reports_the_bad_row_alongside_successfully_parsed_rows(self):
        # parse_csv_rows itself returns partial results (both the rows that
        # parsed fine and the ones that didn't) - it's the API layer
        # (import_bills) that enforces all-or-nothing by discarding `bills`
        # whenever `errors` is non-empty, never calling this twice.
        csv_text = (
            "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
            "start_date,end_date,enabled,notes\n"
            "Rent,100.00,monthly,,,2026-01-01,,true,\n"
            ",50.00,monthly,,,2026-01-01,,true,\n"
        )
        bills, errors = parse_csv_rows(csv_text)

        assert len(bills) == 1
        assert bills[0].name == "Rent"
        assert len(errors) == 1
        assert errors[0].row == 3

    def test_short_row_with_missing_trailing_columns_does_not_crash(self):
        # csv.DictReader fills missing trailing fields with None (not ""),
        # which previously crashed with AttributeError on `.strip()`.
        csv_text = "name,amount,recurrence_type,semimonthly_days,custom_interval_days,start_date\nRent,100.00,monthly\n"
        bills, errors = parse_csv_rows(csv_text)

        assert bills == []
        assert len(errors) == 1
        assert "start_date" in errors[0].message

    def test_enabled_defaults_to_true_when_blank(self):
        csv_text = (
            "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
            "start_date,end_date,enabled,notes\n"
            "Rent,100.00,monthly,,,2026-01-01,,,\n"
        )
        bills, errors = parse_csv_rows(csv_text)

        assert errors == []
        assert bills[0].enabled is True
