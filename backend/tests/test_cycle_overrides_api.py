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


async def _create_windfall(client: AsyncClient, account_id: int, **overrides) -> dict:
    payload = {"name": "Bonus", "amount_cents": 50000, "expected_date": "2024-01-20"}
    payload.update(overrides)
    res = await client.post(f"/api/v1/accounts/{account_id}/windfalls", json=payload)
    return res.json()


async def test_upsert_creates_override_for_bill(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2024-01-15",
            "completed": True,
            "override_amount_cents": 160000,
            "notes": "rent went up",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["completed"] is True
    assert body["override_amount_cents"] == 160000
    assert body["notes"] == "rent went up"
    assert body["windfall_id"] is None


async def test_upsert_updates_existing_override_by_composite_key(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    base_payload = {
        "account_id": account["id"],
        "bill_id": bill["id"],
        "cycle_start_date": "2024-01-15",
    }

    first = await client.put("/api/v1/cycle-overrides", json={**base_payload, "completed": True})
    second = await client.put(
        "/api/v1/cycle-overrides",
        json={**base_payload, "completed": True, "override_amount_cents": 99999},
    )
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["override_amount_cents"] == 99999

    res = await client.get(
        f"/api/v1/accounts/{account['id']}/cycle-overrides", params={"cycle_start": "2024-01-15"}
    )
    assert len(res.json()) == 1


async def test_upsert_creates_override_for_windfall(client: AsyncClient):
    account = await _create_account(client)
    windfall = await _create_windfall(client, account["id"])

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "windfall_id": windfall["id"],
            "cycle_start_date": "2024-01-01",
            "completed": True,
        },
    )
    assert res.status_code == 200
    assert res.json()["bill_id"] is None
    assert res.json()["windfall_id"] == windfall["id"]


async def test_upsert_rejects_both_bill_and_windfall_set(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    windfall = await _create_windfall(client, account["id"])

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "windfall_id": windfall["id"],
            "cycle_start_date": "2024-01-15",
        },
    )
    assert res.status_code == 422


async def test_upsert_rejects_neither_bill_nor_windfall_set(client: AsyncClient):
    account = await _create_account(client)

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={"account_id": account["id"], "cycle_start_date": "2024-01-15"},
    )
    assert res.status_code == 422


async def test_upsert_rejects_bill_from_another_account(client: AsyncClient):
    account = await _create_account(client)
    other_account = await _create_account(client)
    bill = await _create_bill(client, other_account["id"])

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2024-01-15",
        },
    )
    assert res.status_code == 404


async def test_cycle_overrides_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2024-01-15",
            "completed": True,
        },
    )

    _login_as("auth0|someone-else")
    res = await client.get(
        f"/api/v1/accounts/{account['id']}/cycle-overrides", params={"cycle_start": "2024-01-15"}
    )
    assert res.status_code == 404

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2024-01-15",
            "completed": True,
        },
    )
    assert res.status_code == 404
