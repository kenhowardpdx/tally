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


async def test_create_bill_rejects_notes_over_max_length(client: AsyncClient):
    account = await _create_account(client)

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/bills",
        json=_bill_payload(notes="x" * 1001),
    )
    assert res.status_code == 422


async def test_create_bill_rejects_invalid_recurrence_config(client: AsyncClient):
    account = await _create_account(client)

    res = await client.post(
        f"/api/v1/accounts/{account['id']}/bills",
        json=_bill_payload(recurrence_type="custom_days", recurrence_config={}),
    )
    assert res.status_code == 422
    assert "interval_days" in res.json()["detail"]

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.json() == []


async def test_update_bill_rejects_invalid_recurrence_config(client: AsyncClient):
    account = await _create_account(client)
    bill = (
        await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}",
        json={"recurrence_type": "semimonthly"},
    )
    assert res.status_code == 422
    assert "days" in res.json()["detail"]


async def test_update_bill_unrelated_field_keeps_existing_valid_recurrence_config(
    client: AsyncClient,
):
    account = await _create_account(client)
    bill = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/bills",
            json=_bill_payload(recurrence_type="semimonthly", recurrence_config={"days": [10, 25]}),
        )
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}",
        json={"amount_cents": 99999},
    )
    assert res.status_code == 200
    assert res.json()["amount_cents"] == 99999
    assert res.json()["recurrence_config"] == {"days": [10, 25]}


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


async def test_bill_past_end_date_auto_disabled_on_list(client: AsyncClient):
    account = await _create_account(client)
    past_end_date = date.today() - timedelta(days=1)
    bill = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/bills",
            json=_bill_payload(end_date=past_end_date.isoformat()),
        )
    ).json()
    assert bill["enabled"] is True

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.status_code == 200
    assert res.json()[0]["enabled"] is False

    events_res = await client.get(f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/events")
    event_types = [e["event_type"] for e in events_res.json()["events"]]
    assert event_types == ["disabled", "created"]


async def test_bill_future_end_date_stays_enabled_on_list(client: AsyncClient):
    account = await _create_account(client)
    future_end_date = date.today() + timedelta(days=1)
    bill = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/bills",
            json=_bill_payload(end_date=future_end_date.isoformat()),
        )
    ).json()

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.json()[0]["enabled"] is True
    assert bill["enabled"] is True


async def test_manually_disabled_bill_past_end_date_not_double_flagged(client: AsyncClient):
    account = await _create_account(client)
    past_end_date = date.today() - timedelta(days=1)
    bill = (
        await client.post(
            f"/api/v1/accounts/{account['id']}/bills",
            json=_bill_payload(end_date=past_end_date.isoformat(), enabled=False),
        )
    ).json()

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.json()[0]["enabled"] is False

    events_res = await client.get(f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/events")
    event_types = [e["event_type"] for e in events_res.json()["events"]]
    assert event_types == ["created"]


async def test_delete_bill(client: AsyncClient):
    account = await _create_account(client)
    bill = (
        await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    ).json()

    res = await client.delete(f"/api/v1/accounts/{account['id']}/bills/{bill['id']}")
    assert res.status_code == 204

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.json() == []


async def test_move_bill_to_another_owned_account(client: AsyncClient):
    account_a = await _create_account(client)
    account_b = (await client.post("/api/v1/accounts", json={"name": "Savings"})).json()
    bill = (
        await client.post(f"/api/v1/accounts/{account_a['id']}/bills", json=_bill_payload())
    ).json()

    res = await client.patch(
        f"/api/v1/accounts/{account_a['id']}/bills/{bill['id']}",
        json={"account_id": account_b["id"]},
    )
    assert res.status_code == 200
    assert res.json()["account_id"] == account_b["id"]

    res = await client.get(f"/api/v1/accounts/{account_a['id']}/bills")
    assert res.json() == []
    res = await client.get(f"/api/v1/accounts/{account_b['id']}/bills")
    assert len(res.json()) == 1


async def test_cannot_move_bill_to_another_users_account(client: AsyncClient):
    account = await _create_account(client)
    bill = (
        await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    ).json()

    _login_as("auth0|someone-else")
    other_account = (await client.post("/api/v1/accounts", json={"name": "Their account"})).json()
    _login_as("auth0|owner")

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}",
        json={"account_id": other_account["id"]},
    )
    assert res.status_code == 404


async def test_bills_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())

    _login_as("auth0|someone-else")
    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.status_code == 404

    res = await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())
    assert res.status_code == 404


async def test_export_bills_returns_csv(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills/export")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment" in res.headers["content-disposition"]
    lines = res.text.strip().splitlines()
    assert len(lines) == 2  # header + one bill
    assert "Rent" in lines[1]
    assert "1500.00" in lines[1]


async def test_export_bills_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    await client.post(f"/api/v1/accounts/{account['id']}/bills", json=_bill_payload())

    _login_as("auth0|someone-else")
    res = await client.get(f"/api/v1/accounts/{account['id']}/bills/export")
    assert res.status_code == 404


async def test_import_bills_creates_all_rows(client: AsyncClient):
    account = await _create_account(client)
    csv_text = (
        "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
        "start_date,end_date,enabled,notes\n"
        "Rent,1500.00,monthly,,,2026-01-01,,true,\n"
        "Paycheck buffer,50.00,semimonthly,\"10,25\",,2026-01-01,,true,imported\n"
    )
    res = await client.post(
        f"/api/v1/accounts/{account['id']}/bills/import",
        files={"file": ("bills.csv", csv_text, "text/csv")},
    )
    assert res.status_code == 201
    body = res.json()
    assert len(body) == 2
    assert {b["name"] for b in body} == {"Rent", "Paycheck buffer"}
    semimonthly = next(b for b in body if b["name"] == "Paycheck buffer")
    assert semimonthly["recurrence_config"] == {"days": [10, 25]}
    assert semimonthly["notes"] == "imported"

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert len(res.json()) == 2


async def test_import_bills_is_all_or_nothing_on_a_bad_row(client: AsyncClient):
    account = await _create_account(client)
    csv_text = (
        "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
        "start_date,end_date,enabled,notes\n"
        "Rent,1500.00,monthly,,,2026-01-01,,true,\n"
        ",50.00,monthly,,,2026-01-01,,true,\n"
    )
    res = await client.post(
        f"/api/v1/accounts/{account['id']}/bills/import",
        files={"file": ("bills.csv", csv_text, "text/csv")},
    )
    assert res.status_code == 422
    errors = res.json()["detail"]["errors"]
    assert len(errors) == 1
    assert errors[0]["row"] == 3

    res = await client.get(f"/api/v1/accounts/{account['id']}/bills")
    assert res.json() == []


async def test_import_bills_scoped_to_account_owner(client: AsyncClient):
    account = await _create_account(client)
    csv_text = (
        "name,amount,recurrence_type,semimonthly_days,custom_interval_days,"
        "start_date,end_date,enabled,notes\n"
        "Rent,1500.00,monthly,,,2026-01-01,,true,\n"
    )

    _login_as("auth0|someone-else")
    res = await client.post(
        f"/api/v1/accounts/{account['id']}/bills/import",
        files={"file": ("bills.csv", csv_text, "text/csv")},
    )
    assert res.status_code == 404
