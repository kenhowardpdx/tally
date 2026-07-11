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


def _bill_payload(**overrides) -> dict:
    payload = {
        "name": "Rent",
        "amount_cents": 150000,
        "recurrence_type": "monthly",
        "recurrence_config": {"day_of_month": 1},
        "start_date": "2026-01-01",
    }
    payload.update(overrides)
    return payload


async def test_create_and_list_bills(client: AsyncClient):
    account = await _create_account(client)

    res = await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Rent"
    assert body["enabled"] is True

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.status_code == 200
    assert len(res.json()) == 1


async def test_toggle_bill_enabled(client: AsyncClient):
    account = await _create_account(client)
    bill = (
        await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}", json={"enabled": False}
    )
    assert res.status_code == 200
    assert res.json()["enabled"] is False


async def test_delete_bill(client: AsyncClient):
    account = await _create_account(client)
    bill = (
        await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    ).json()

    res = await client.delete(f"/api/v1/accounts/{account['id']}/bills/{bill['id']}")
    assert res.status_code == 204

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.json() == []


async def test_bills_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())

    _login_as("auth0|someone-else")
    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.status_code == 404

    res = await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    assert res.status_code == 404
