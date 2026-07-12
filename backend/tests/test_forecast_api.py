from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.main import app
from src.models import Bill, RecurrenceType
from tests.conftest import auth_as


def _login_as(sub: str) -> None:
    app.dependency_overrides[get_current_user] = auth_as(sub)


@pytest.fixture(autouse=True)
def _default_user():
    _login_as("auth0|owner")
    yield
    app.dependency_overrides.pop(get_current_user, None)


async def _create_account(client: AsyncClient) -> dict:
    res = await client.post("/api/v1/accounts", json={"name": "Checking"})
    return res.json()


def _bill_payload(**overrides) -> dict:
    payload = {
        "name": "Rent",
        "amount_cents": 150000,
        "recurrence_type": "monthly",
        "start_date": "2024-01-15",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _forecast_payload(**overrides) -> dict:
    payload = {
        "start_date": "2024-01-01",
        "end_date": "2024-02-29",
        "starting_balance_cents": 100000,
        "income_per_cycle_cents": 200000,
        "cycle_type": "monthly",
    }
    payload.update(overrides)
    return payload


async def test_forecast_computes_cycles_and_running_balance(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/forecast", json=_forecast_payload()
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["cycles"]) == 2
    assert body["cycles"][0]["bills"][0]["name"] == "Rent"
    # 100000 + 200000*2 - 150000*2 = 200000
    assert body["ending_balance_cents"] == 200000
    assert body["unscheduled_bills"] == []


async def test_forecast_includes_transactions_and_windfalls(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    await client.post(
        f"/api/v1/accounts/{account['id']}/transactions",
        json={"amount_cents": -2000, "date": "2024-01-10", "description": "oops"},
    )
    await client.post(
        f"/api/v1/accounts/{account['id']}/windfalls",
        json={"name": "bonus", "amount_cents": 50000, "expected_date": "2024-01-20"},
    )

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/forecast",
        json=_forecast_payload(end_date="2024-01-31"),
    )
    assert res.status_code == 200
    body = res.json()
    first_cycle = body["cycles"][0]
    assert len(first_cycle["transactions"]) == 1
    assert len(first_cycle["windfalls"]) == 1
    # -150000 (bill) - 2000 (transaction) + 50000 (windfall)
    assert first_cycle["net_cents"] == -102000
    assert body["ending_balance_cents"] == 100000 + 200000 - 102000


async def test_forecast_excludes_disabled_bills(client: AsyncClient):
    account = await _create_account(client)
    await client.post(
        f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload(enabled=False)
    )

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/forecast", json=_forecast_payload()
    )
    assert res.status_code == 200
    body = res.json()
    assert all(cycle["bills"] == [] for cycle in body["cycles"])
    assert body["ending_balance_cents"] == 100000 + 200000 * 2


async def test_forecast_reports_bills_missing_recurrence_config(
    client: AsyncClient, db_session: AsyncSession
):
    # create_bill now rejects a missing/invalid recurrence_config outright
    # (422), so a bill can only end up in this state via data that predates
    # that validation (or a direct DB write) - insert one directly to
    # exercise the forecast engine's defensive unscheduled_bills handling.
    account = await _create_account(client)
    bill = Bill(
        account_id=account["id"],
        name="Rent",
        amount_cents=150000,
        recurrence_type=RecurrenceType.CUSTOM_DAYS,
        recurrence_config={},
        start_date=date(2024, 1, 15),
        enabled=True,
    )
    db_session.add(bill)
    await db_session.commit()

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/forecast", json=_forecast_payload()
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["unscheduled_bills"]) == 1
    assert "interval_days" in body["unscheduled_bills"][0]["reason"]


async def test_forecast_persists_settings_onto_account(client: AsyncClient):
    account = await _create_account(client)

    payload = _forecast_payload()
    res = await client.post(f"/api/v1/accounts/{account['id']}/forecast", json=payload)
    assert res.status_code == 200

    res = await client.get(f"/api/v1/accounts/{account['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["forecast_starting_balance_cents"] == payload["starting_balance_cents"]
    assert body["forecast_income_per_cycle_cents"] == payload["income_per_cycle_cents"]
    assert body["forecast_cycle_type"] == payload["cycle_type"]
    assert body["forecast_start_date"] == payload["start_date"]
    assert body["forecast_end_date"] == payload["end_date"]


async def test_forecast_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)

    _login_as("auth0|someone-else")
    res = await client.post(
        f"/api/v1/accounts/{account['id']}/forecast", json=_forecast_payload()
    )
    assert res.status_code == 404


async def test_forecast_end_date_before_start_date_is_rejected(client: AsyncClient):
    account = await _create_account(client)

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/forecast",
        json=_forecast_payload(start_date="2024-02-01", end_date="2024-01-01"),
    )
    assert res.status_code == 422
