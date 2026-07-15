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


async def _create_bill(client: AsyncClient, account_id: int, **overrides) -> dict:
    payload = {
        "name": "Rent",
        "amount_cents": 150000,
        "recurrence_type": "monthly",
        "start_date": "2024-01-01",
    }
    payload.update(overrides)
    res = await client.post(f"/api/v1/accounts/{account_id}/bills", json=payload)
    return res.json()


async def _preview(client: AsyncClient, account_id: int, csv_text: str):
    return await client.post(
        f"/api/v1/accounts/{account_id}/transactions/import/preview",
        files={"file": ("transactions.csv", csv_text, "text/csv")},
    )


async def test_export_transactions_includes_linked_bill_name(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    await client.post(
        f"/api/v1/accounts/{account['id']}/transactions",
        json=_transaction_payload(bill_id=bill["id"]),
    )

    res = await client.get(f"/api/v1/accounts/{account['id']}/transactions/export")
    assert res.status_code == 200
    assert "bill_name" in res.text
    assert "Rent" in res.text


async def test_preview_transaction_import_resolves_bill_name_to_bill_id(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    csv_text = "date,amount,description,bill_name\n2024-01-15,-25.00,Coffee,Rent\n"

    res = await _preview(client, account["id"], csv_text)
    assert res.status_code == 200
    body = res.json()
    assert len(body["new"]) == 1
    assert body["new"][0]["bill_id"] == bill["id"]
    assert body["warnings"] == []


async def test_preview_transaction_import_warns_on_unresolved_bill_name(client: AsyncClient):
    account = await _create_account(client)
    csv_text = "date,amount,description,bill_name\n2024-01-15,-25.00,Coffee,Nonexistent\n"

    res = await _preview(client, account["id"], csv_text)
    body = res.json()
    assert body["new"][0]["bill_id"] is None
    assert len(body["warnings"]) == 1
    assert "Nonexistent" in body["warnings"][0]["message"]


async def test_preview_transaction_import_warns_on_ambiguous_bill_name(client: AsyncClient):
    account = await _create_account(client)
    await _create_bill(client, account["id"])
    await _create_bill(client, account["id"])
    csv_text = "date,amount,description,bill_name\n2024-01-15,-25.00,Coffee,Rent\n"

    res = await _preview(client, account["id"], csv_text)
    body = res.json()
    assert body["new"][0]["bill_id"] is None
    assert len(body["warnings"]) == 1
    assert "Rent" in body["warnings"][0]["message"]


async def test_commit_transaction_import_creates_new_rows(client: AsyncClient):
    account = await _create_account(client)
    payload = {
        "new": [{"amount_cents": -2500, "date": "2024-01-15", "description": "Coffee", "bill_id": None}],
        "updated": [],
        "omitted_ids": [],
    }
    res = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions/import/commit", json=payload
    )
    assert res.status_code == 200
    assert len(res.json()["created"]) == 1

    res = await client.get(f"/api/v1/accounts/{account['id']}/transactions")
    assert len(res.json()) == 1


async def test_reimporting_unmodified_export_is_all_unchanged(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload())

    export_res = await client.get(f"/api/v1/accounts/{account['id']}/transactions/export")
    res = await _preview(client, account["id"], export_res.text)
    body = res.json()
    assert body["new"] == []
    assert body["updated"] == []
    assert body["unchanged_count"] == 1
    assert body["omitted"] == []


async def test_reimporting_with_new_bill_link_shows_as_updated(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    await client.post(f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload())

    csv_text = f"date,amount,description,bill_name\n2024-01-15,-25.00,Coffee,{bill['name']}\n"
    res = await _preview(client, account["id"], csv_text)
    body = res.json()
    assert body["new"] == []
    assert len(body["updated"]) == 1
    assert body["updated"][0]["fields"]["bill_id"] == bill["id"]


async def test_transaction_omitted_from_csv_is_hard_deleted(client: AsyncClient):
    account = await _create_account(client)
    kept = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions", json=_transaction_payload()
    )
    dropped = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions",
        json=_transaction_payload(description="Groceries", amount_cents=-5000),
    )
    dropped_id = dropped.json()["id"]

    csv_text = "date,amount,description,bill_name\n2024-01-15,-25.00,Coffee,\n"
    preview = (await _preview(client, account["id"], csv_text)).json()
    assert len(preview["omitted"]) == 1
    assert preview["omitted"][0]["id"] == dropped_id

    commit_res = await client.post(
        f"/api/v1/accounts/{account['id']}/transactions/import/commit",
        json={"new": [], "updated": [], "omitted_ids": [row["id"] for row in preview["omitted"]]},
    )
    assert commit_res.status_code == 200
    assert commit_res.json()["deleted_count"] == 1

    list_res = await client.get(f"/api/v1/accounts/{account['id']}/transactions")
    descriptions = {t["description"] for t in list_res.json()}
    assert descriptions == {"Coffee"}

    assert kept.status_code == 201  # sanity: the "kept" transaction was actually created


async def test_preview_transaction_import_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    csv_text = "date,amount,description,bill_name\n2024-01-15,-25.00,Coffee,\n"

    _login_as("auth0|someone-else")
    res = await _preview(client, account["id"], csv_text)
    assert res.status_code == 404
