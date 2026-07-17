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


def _windfall_payload(**overrides) -> dict:
    payload = {
        "name": "Tax refund",
        "amount_cents": 50000,
        "expected_date": "2024-04-15",
    }
    payload.update(overrides)
    return payload


async def test_create_and_list_windfalls(client: AsyncClient):
    account = await _create_account(client)

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
    )
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Tax refund"
    assert body["amount_cents"] == 50000

    res = await client.get(f"/api/v1/accounts/{account['id']}/windfalls")
    assert res.status_code == 200
    assert len(res.json()) == 1


async def test_list_windfalls_orders_soonest_first(client: AsyncClient):
    account = await _create_account(client)
    for d in ("2024-06-01", "2024-04-15", "2024-05-01"):
        await client.post(
            f"/api/v1/accounts/{account['id']}/windfalls",
            json=_windfall_payload(expected_date=d),
        )

    res = await client.get(f"/api/v1/accounts/{account['id']}/windfalls")
    dates = [w["expected_date"] for w in res.json()]
    assert dates == ["2024-04-15", "2024-05-01", "2024-06-01"]


async def test_update_windfall(client: AsyncClient):
    account = await _create_account(client)
    windfall = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
        )
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/windfalls/{windfall['id']}",
        json={"amount_cents": 75000},
    )
    assert res.status_code == 200
    assert res.json()["amount_cents"] == 75000


async def test_move_windfall_to_another_owned_account(client: AsyncClient):
    account_a = await _create_account(client)
    account_b = (await client.post("/api/v1/accounts", json={"name": "Savings"})).json()
    windfall = (
        await client.post(
            f"/api/v1/accounts/{account_a['id']}/windfalls", json=_windfall_payload()
        )
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account_a['id']}/windfalls/{windfall['id']}",
        json={"account_id": account_b["id"]},
    )
    assert res.status_code == 200
    assert res.json()["account_id"] == account_b["id"]

    res = await client.get(f"/api/v1/accounts/{account_a['id']}/windfalls")
    assert res.json() == []
    res = await client.get(f"/api/v1/accounts/{account_b['id']}/windfalls")
    assert len(res.json()) == 1


async def test_cannot_move_windfall_to_another_users_account(client: AsyncClient):
    account = await _create_account(client)
    windfall = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
        )
    ).json()

    _login_as("auth0|someone-else")
    other_account = (await client.post("/api/v1/accounts", json={"name": "Their account"})).json()
    _login_as("auth0|owner")

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/windfalls/{windfall['id']}",
        json={"account_id": other_account["id"]},
    )
    assert res.status_code == 404


async def test_update_windfall_rejects_explicit_null_on_required_field(client: AsyncClient):
    account = await _create_account(client)
    windfall = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
        )
    ).json()

    for field in ("name", "amount_cents", "expected_date"):
        res = await client.patch(
            f"/api/v1/accounts/{account['id']}/windfalls/{windfall['id']}",
            json={field: None},
        )
        assert res.status_code == 422


async def test_delete_windfall(client: AsyncClient):
    account = await _create_account(client)
    windfall = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
        )
    ).json()

    res = await client.delete(f"/api/v1/accounts/{account['id']}/windfalls/{windfall['id']}")
    assert res.status_code == 204

    res = await client.get(f"/api/v1/accounts/{account['id']}/windfalls")
    assert res.json() == []


async def test_windfalls_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload())

    _login_as("auth0|someone-else")
    res = await client.get(f"/api/v1/accounts/{account['id']}/windfalls")
    assert res.status_code == 404

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
    )
    assert res.status_code == 404


async def _preview(client: AsyncClient, account_id: int, csv_text: str):
    return await client.post(
        f"/api/v1/accounts/{account_id}/windfalls/import/preview",
        files={"file": ("windfalls.csv", csv_text, "text/csv")},
    )


async def test_preview_windfall_import_buckets_new_rows(client: AsyncClient):
    account = await _create_account(client)
    csv_text = "name,amount,expected_date,enabled\nTax refund,500.00,2024-04-15,true\n"

    res = await _preview(client, account["id"], csv_text)
    assert res.status_code == 200
    body = res.json()
    assert len(body["new"]) == 1
    assert body["new"][0]["name"] == "Tax refund"
    assert body["updated"] == []
    assert body["unchanged_count"] == 0
    assert body["omitted"] == []


async def test_commit_windfall_import_creates_new_rows(client: AsyncClient):
    account = await _create_account(client)
    payload = {
        "new": [
            {
                "name": "Tax refund",
                "amount_cents": 50000,
                "expected_date": "2024-04-15",
                "enabled": True,
            }
        ],
        "updated": [],
        "omitted_ids": [],
    }
    res = await client.post(f"/api/v1/accounts/{account['id']}/windfalls/import/commit", json=payload)
    assert res.status_code == 200
    assert len(res.json()["created"]) == 1

    res = await client.get(f"/api/v1/accounts/{account['id']}/windfalls")
    assert len(res.json()) == 1


async def test_reimporting_unmodified_export_is_all_unchanged(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload())

    export_res = await client.get(f"/api/v1/accounts/{account['id']}/windfalls/export")
    res = await _preview(client, account["id"], export_res.text)
    body = res.json()
    assert body["new"] == []
    assert body["updated"] == []
    assert body["unchanged_count"] == 1
    assert body["omitted"] == []


async def test_windfall_omitted_from_csv_is_disabled_not_deleted(client: AsyncClient):
    account = await _create_account(client)
    kept = await client.post(
        f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
    )
    dropped = await client.post(
        f"/api/v1/accounts/{account['id']}/windfalls",
        json=_windfall_payload(name="Bonus", amount_cents=100000, expected_date="2024-12-01"),
    )
    dropped_id = dropped.json()["id"]

    csv_text = "name,amount,expected_date,enabled\nTax refund,500.00,2024-04-15,true\n"
    preview = (await _preview(client, account["id"], csv_text)).json()
    assert len(preview["omitted"]) == 1
    assert preview["omitted"][0]["id"] == dropped_id

    commit_res = await client.post(
        f"/api/v1/accounts/{account['id']}/windfalls/import/commit",
        json={"new": [], "updated": [], "omitted_ids": [row["id"] for row in preview["omitted"]]},
    )
    assert commit_res.status_code == 200
    assert commit_res.json()["disabled_count"] == 1

    # Still exists, just disabled - not deleted.
    list_res = await client.get(f"/api/v1/accounts/{account['id']}/windfalls")
    enabled_by_name = {w["name"]: w["enabled"] for w in list_res.json()}
    assert enabled_by_name == {"Tax refund": True, "Bonus": False}

    assert kept.status_code == 201  # sanity: the "kept" windfall was actually created


async def test_disabled_windfall_excluded_from_forecast(client: AsyncClient):
    account = await _create_account(client)
    windfall = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/windfalls", json=_windfall_payload()
        )
    ).json()
    await client.patch(
        f"/api/v1/accounts/{account['id']}/windfalls/{windfall['id']}", json={"enabled": False}
    )

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/forecast",
        json={
            "starting_balance_cents": 100000,
            "income_per_cycle_cents": 0,
            "cycle_type": "monthly",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        },
    )
    assert res.status_code == 200
    all_windfall_ids = {
        w["windfall_id"] for cycle in res.json()["cycles"] for w in cycle.get("windfalls", [])
    }
    assert windfall["id"] not in all_windfall_ids


async def test_preview_windfall_import_flags_ambiguous_matches(client: AsyncClient):
    account = await _create_account(client)
    duplicate_payload = _windfall_payload()
    await client.post(f"/api/v1/accounts/{account['id']}/windfalls", json=duplicate_payload)
    await client.post(f"/api/v1/accounts/{account['id']}/windfalls", json=duplicate_payload)

    csv_text = "name,amount,expected_date,enabled\nTax refund,500.00,2024-04-15,true\n"
    res = await _preview(client, account["id"], csv_text)
    body = res.json()
    assert body["new"] == []
    assert body["updated"] == []
    assert len(body["ambiguous"]) == 1
    assert "matches 2 existing windfalls" in body["ambiguous"][0]["message"]


async def test_preview_windfall_import_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    csv_text = "name,amount,expected_date,enabled\nTax refund,500.00,2024-04-15,true\n"

    _login_as("auth0|someone-else")
    res = await _preview(client, account["id"], csv_text)
    assert res.status_code == 404
