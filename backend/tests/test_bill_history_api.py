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


async def _create_account(client: AsyncClient) -> dict:
    res = await client.post("/api/v1/accounts", json={"name": "Checking"})
    return res.json()


async def _create_bill(client: AsyncClient, account_id: int, **overrides) -> dict:
    payload = {
        "name": "Rent",
        "amount_cents": 150000,
        "recurrence_type": "monthly",
        "start_date": "2024-01-15",
        "enabled": True,
    }
    payload.update(overrides)
    res = await client.post(f"/api/v1/accounts/{account_id}/bills", json=payload)
    return res.json()


async def test_history_lists_one_entry_per_monthly_occurrence(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.get(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/history",
        params={
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "cycle_type": "monthly",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["bill_id"] == bill["id"]
    assert body["total"] == 3
    # Most recent first.
    assert [e["due_date"] for e in body["entries"]] == ["2024-03-15", "2024-02-15", "2024-01-15"]
    assert all(e["expected_amount_cents"] == 150000 for e in body["entries"])
    assert all(e["actual_amount_cents"] == 150000 for e in body["entries"])
    assert all(e["variance_cents"] == 0 for e in body["entries"])
    assert all(e["completed"] is False for e in body["entries"])


async def test_history_reflects_override_amount_and_completed(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2024-02-01",
            "completed": True,
            "override_amount_cents": 160000,
            "notes": "rent went up",
        },
    )

    res = await client.get(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/history",
        params={
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "cycle_type": "monthly",
        },
    )
    assert res.status_code == 200
    entries = {e["due_date"]: e for e in res.json()["entries"]}
    assert entries["2024-02-15"]["actual_amount_cents"] == 160000
    assert entries["2024-02-15"]["completed"] is True
    assert entries["2024-02-15"]["notes"] == "rent went up"
    assert entries["2024-02-15"]["variance_cents"] == 10000
    assert entries["2024-01-15"]["actual_amount_cents"] == 150000
    assert entries["2024-01-15"]["completed"] is False


async def test_history_pagination(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.get(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/history",
        params={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "cycle_type": "monthly",
            "limit": 2,
            "offset": 0,
        },
    )
    body = res.json()
    assert body["total"] == 12
    assert len(body["entries"]) == 2
    assert body["entries"][0]["due_date"] == "2024-12-15"


async def test_history_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    _login_as("auth0|someone-else")
    res = await client.get(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/history",
        params={"start_date": "2024-01-01", "end_date": "2024-03-31"},
    )
    assert res.status_code == 404


async def test_history_end_before_start_is_rejected(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.get(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/history",
        params={"start_date": "2024-03-01", "end_date": "2024-01-01"},
    )
    assert res.status_code == 422
