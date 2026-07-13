from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from src.core.auth import get_current_user
from src.main import app
from tests.conftest import auth_as


def _login_as(sub: str) -> None:
    app.dependency_overrides[get_current_user] = auth_as(sub)


@pytest.fixture(autouse=True)
def _default_user():
    _login_as("auth0|owner")
    yield
    app.dependency_overrides.pop(get_current_user, None)


async def _create_account(client: AsyncClient, **overrides) -> dict:
    payload = {"name": "Checking"}
    payload.update(overrides)
    res = await client.post("/api/v1/accounts", json=payload)
    return res.json()


def _iso(d: date) -> str:
    return d.isoformat()


async def test_dashboard_reports_unconfigured_account(client: AsyncClient):
    await _create_account(client)

    res = await client.get("/api/v1/dashboard")
    assert res.status_code == 200
    body = res.json()
    assert len(body["accounts"]) == 1
    assert body["accounts"][0]["configured"] is False
    assert body["accounts"][0]["cycle_start_date"] is None
    assert body["combined_ending_balance_cents"] == 0


async def test_dashboard_current_cycle_reflects_last_forecast_run(client: AsyncClient):
    account = await _create_account(client)
    today = date.today()
    # A monthly cycle anchored well in the past so "today" always falls
    # somewhere in the middle of the generated cycle sequence, not the first
    # or last cycle - exercises the actual current-cycle search.
    anchor = today.replace(day=1) - timedelta(days=400)
    await client.post(
        f"/api/v1/accounts/{account['id']}/bills",
        json={
            "name": "Rent",
            "amount_cents": 120000,
            "recurrence_type": "monthly",
            "start_date": _iso(anchor),
            "enabled": True,
        },
    )
    await client.post(
        f"/api/v1/accounts/{account['id']}/forecast",
        json={
            "start_date": _iso(anchor),
            "end_date": _iso(anchor + timedelta(days=30)),
            "starting_balance_cents": 500000,
            "income_per_cycle_cents": 200000,
            "cycle_type": "monthly",
        },
    )

    res = await client.get("/api/v1/dashboard")
    assert res.status_code == 200
    summary = res.json()["accounts"][0]
    assert summary["configured"] is True
    assert summary["is_upcoming"] is False
    assert summary["cycle_type"] == "monthly"
    assert summary["cycle_start_date"] <= _iso(today) <= summary["cycle_end_date"]
    assert any(bill["name"] == "Rent" for bill in summary["bills"])
    assert res.json()["combined_ending_balance_cents"] == summary["ending_balance_cents"]


async def test_dashboard_upcoming_when_forecast_start_date_is_in_the_future(client: AsyncClient):
    account = await _create_account(client)
    future = date.today() + timedelta(days=30)
    await client.post(
        f"/api/v1/accounts/{account['id']}/forecast",
        json={
            "start_date": _iso(future),
            "end_date": _iso(future + timedelta(days=13)),
            "starting_balance_cents": 100000,
            "income_per_cycle_cents": 0,
            "cycle_type": "biweekly",
        },
    )

    res = await client.get("/api/v1/dashboard")
    summary = res.json()["accounts"][0]
    assert summary["is_upcoming"] is True
    assert summary["cycle_start_date"] == _iso(future)
    assert summary["starting_balance_cents"] == 100000


async def test_dashboard_combines_multiple_accounts(client: AsyncClient):
    today = date.today()
    for i in range(2):
        account = await _create_account(client, name=f"Account {i}")
        await client.post(
            f"/api/v1/accounts/{account['id']}/forecast",
            json={
                "start_date": _iso(today),
                "end_date": _iso(today + timedelta(days=6)),
                "starting_balance_cents": 10000,
                "income_per_cycle_cents": 0,
                "cycle_type": "weekly",
            },
        )

    res = await client.get("/api/v1/dashboard")
    body = res.json()
    assert len(body["accounts"]) == 2
    assert body["combined_ending_balance_cents"] == sum(
        a["ending_balance_cents"] for a in body["accounts"]
    )


async def test_dashboard_scoped_to_current_user(client: AsyncClient):
    await _create_account(client)

    _login_as("auth0|someone-else")
    res = await client.get("/api/v1/dashboard")
    assert res.status_code == 200
    assert res.json()["accounts"] == []
