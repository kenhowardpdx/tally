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


def _transaction_payload(**overrides) -> dict:
    payload = {
        "amount_cents": -2500,
        "date": "2024-01-15",
        "description": "Coffee",
    }
    payload.update(overrides)
    return payload


async def test_create_and_list_transactions(client: AsyncClient):
    account = await _create_account(client)

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload()
    )
    assert res.status_code == 201
    body = res.json()
    assert body["amount_cents"] == -2500
    assert body["description"] == "Coffee"
    assert body["bill_id"] is None

    res = await client.get(f"/api/v1/accounts/{account['id']}/transactions")
    assert res.status_code == 200
    assert len(res.json()) == 1


async def test_list_transactions_orders_newest_first(client: AsyncClient):
    account = await _create_account(client)
    for d in ("2024-01-01", "2024-03-01", "2024-02-01"):
        await client.post(
            f"/api/v1/accounts/{account['id']}/transactions",
            json=_transaction_payload(date=d),
        )

    res = await client.get(f"/api/v1/accounts/{account['id']}/transactions")
    dates = [t["date"] for t in res.json()]
    assert dates == ["2024-03-01", "2024-02-01", "2024-01-01"]


async def test_update_transaction(client: AsyncClient):
    account = await _create_account(client)
    transaction = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload()
        )
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/transactions/{transaction['id']}",
        json={"amount_cents": 500},
    )
    assert res.status_code == 200
    assert res.json()["amount_cents"] == 500


async def test_move_transaction_to_another_owned_account(client: AsyncClient):
    account_a = await _create_account(client)
    account_b = (await client.post("/api/v1/accounts", json={"name": "Savings"})).json()
    transaction = (
        await client.post(
            f"/api/v1/accounts/{account_a['id']}/transactions", json=_transaction_payload()
        )
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account_a['id']}/transactions/{transaction['id']}",
        json={"account_id": account_b["id"]},
    )
    assert res.status_code == 200
    assert res.json()["account_id"] == account_b["id"]

    res = await client.get(f"/api/v1/accounts/{account_a['id']}/transactions")
    assert res.json() == []
    res = await client.get(f"/api/v1/accounts/{account_b['id']}/transactions")
    assert len(res.json()) == 1


async def test_cannot_move_transaction_to_another_users_account(client: AsyncClient):
    account = await _create_account(client)
    transaction = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload()
        )
    ).json()

    _login_as("auth0|someone-else")
    other_account = (await client.post("/api/v1/accounts", json={"name": "Their account"})).json()
    _login_as("auth0|owner")

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/transactions/{transaction['id']}",
        json={"account_id": other_account["id"]},
    )
    assert res.status_code == 404


async def test_update_transaction_rejects_explicit_null_on_required_field(client: AsyncClient):
    account = await _create_account(client)
    transaction = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload()
        )
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/transactions/{transaction['id']}",
        json={"amount_cents": None},
    )
    assert res.status_code == 422

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/transactions/{transaction['id']}",
        json={"date": None},
    )
    assert res.status_code == 422

    # Nullable fields (description, bill_id) may still be explicitly cleared.
    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/transactions/{transaction['id']}",
        json={"description": None},
    )
    assert res.status_code == 200
    assert res.json()["description"] is None


async def test_delete_transaction(client: AsyncClient):
    account = await _create_account(client)
    transaction = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload()
        )
    ).json()

    res = await client.delete(f"/api/v1/accounts/{account['id']}/transactions/{transaction['id']}")
    assert res.status_code == 204

    res = await client.get(f"/api/v1/accounts/{account['id']}/transactions")
    assert res.json() == []


async def test_transaction_can_link_to_a_bill_in_the_same_account(client: AsyncClient):
    account = await _create_account(client)
    bill = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/bills",
            json={
                "name": "Rent",
                "amount_cents": 150000,
                "recurrence_type": "monthly",
                "start_date": "2024-01-01",
            },
        )
    ).json()

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions",
        json=_transaction_payload(bill_id=bill["id"]),
    )
    assert res.status_code == 201
    assert res.json()["bill_id"] == bill["id"]


async def test_transaction_cannot_link_to_a_bill_in_another_account(client: AsyncClient):
    account = await _create_account(client)
    other_account = (await client.post("/api/v1/accounts", json={"name": "Savings"})).json()
    other_bill = (
        await client.post(
            f"/api/v1/accounts/{other_account['id']}/bills",
            json={
                "name": "Rent",
                "amount_cents": 150000,
                "recurrence_type": "monthly",
                "start_date": "2024-01-01",
            },
        )
    ).json()

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions",
        json=_transaction_payload(bill_id=other_bill["id"]),
    )
    assert res.status_code == 404


async def test_transactions_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload())

    _login_as("auth0|someone-else")
    res = await client.get(f"/api/v1/accounts/{account['id']}/transactions")
    assert res.status_code == 404

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload()
    )
    assert res.status_code == 404
