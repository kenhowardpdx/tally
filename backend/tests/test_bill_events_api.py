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
        "recurrence_config": {"day_of_month": 1},
        "start_date": "2026-01-01",
    }
    payload.update(overrides)
    res = await client.post(f"/api/v1/accounts/{account_id}/bills", json=payload)
    return res.json()


async def _get_events(client: AsyncClient, account_id: int, bill_id: int) -> list[dict]:
    res = await client.get(f"/api/v1/accounts/{account_id}/bills/{bill_id}/events")
    assert res.status_code == 200
    return res.json()["events"]


async def test_creating_a_bill_records_a_created_event(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    events = await _get_events(client, account["id"], bill["id"])
    assert len(events) == 1
    assert events[0]["event_type"] == "created"
    assert events[0]["cycle_start_date"] is None
    assert events[0]["changes"]["amount_cents"] == 150000
    assert events[0]["changes"]["name"] == "Rent"


async def test_updating_amount_records_a_single_updated_event(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}",
        json={"amount_cents": 175000, "name": "Rent (increased)"},
    )
    assert res.status_code == 200

    events = await _get_events(client, account["id"], bill["id"])
    # newest first: the update, then the original creation
    assert [e["event_type"] for e in events] == ["updated", "created"]
    changes = events[0]["changes"]
    assert changes["amount_cents"] == {"old": 150000, "new": 175000}
    assert changes["name"] == {"old": "Rent", "new": "Rent (increased)"}
    assert "notes" not in changes


async def test_updating_notes_records_a_notes_changed_event_separately(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}",
        json={"amount_cents": 175000, "notes": "landlord raised rent"},
    )
    assert res.status_code == 200

    events = await _get_events(client, account["id"], bill["id"])
    types = [e["event_type"] for e in events]
    assert "notes_changed" in types
    assert "updated" in types
    notes_event = next(e for e in events if e["event_type"] == "notes_changed")
    assert notes_event["changes"] == {"notes": {"old": None, "new": "landlord raised rent"}}


async def test_disabling_then_enabling_a_bill_records_distinct_events(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}", json={"enabled": False}
    )
    await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}", json={"enabled": True}
    )

    events = await _get_events(client, account["id"], bill["id"])
    assert [e["event_type"] for e in events] == ["enabled", "disabled", "created"]


async def test_no_op_update_records_no_event(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.patch(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}", json={"amount_cents": 150000}
    )
    assert res.status_code == 200

    events = await _get_events(client, account["id"], bill["id"])
    assert [e["event_type"] for e in events] == ["created"]


async def test_cycle_override_marks_paid_and_sets_amount_and_notes(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2026-01-01",
            "completed": True,
            "override_amount_cents": 160000,
            "notes": "landlord waived late fee",
        },
    )
    assert res.status_code == 200

    events = await _get_events(client, account["id"], bill["id"])
    types = [e["event_type"] for e in events]
    assert "cycle_marked_paid" in types
    assert "cycle_amount_changed" in types
    assert "cycle_notes_changed" in types

    amount_event = next(e for e in events if e["event_type"] == "cycle_amount_changed")
    assert amount_event["cycle_start_date"] == "2026-01-01"
    assert amount_event["changes"] == {"override_amount_cents": {"old": None, "new": 160000}}

    notes_event = next(e for e in events if e["event_type"] == "cycle_notes_changed")
    assert notes_event["changes"] == {"notes": {"old": None, "new": "landlord waived late fee"}}


async def test_cycle_override_unmarking_paid_records_unpaid_event(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2026-01-01",
            "completed": True,
        },
    )
    await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "bill_id": bill["id"],
            "cycle_start_date": "2026-01-01",
            "completed": False,
        },
    )

    events = await _get_events(client, account["id"], bill["id"])
    assert events[0]["event_type"] == "cycle_marked_unpaid"
    assert events[1]["event_type"] == "cycle_marked_paid"


async def test_cycle_override_resubmitting_same_values_records_no_new_events(
    client: AsyncClient,
):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    payload = {
        "account_id": account["id"],
        "bill_id": bill["id"],
        "cycle_start_date": "2026-01-01",
        "completed": True,
        "override_amount_cents": 160000,
    }
    await client.put("/api/v1/cycle-overrides", json=payload)
    events_after_first = await _get_events(client, account["id"], bill["id"])

    await client.put("/api/v1/cycle-overrides", json=payload)
    events_after_second = await _get_events(client, account["id"], bill["id"])

    assert len(events_after_second) == len(events_after_first)


async def test_windfall_cycle_override_does_not_create_bill_events(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    windfall_res = await client.post(
        f"/api/v1/accounts/{account['id']}/windfalls",
        json={"name": "Bonus", "amount_cents": 50000, "expected_date": "2026-01-15"},
    )
    windfall = windfall_res.json()

    res = await client.put(
        "/api/v1/cycle-overrides",
        json={
            "account_id": account["id"],
            "windfall_id": windfall["id"],
            "cycle_start_date": "2026-01-01",
            "completed": True,
        },
    )
    assert res.status_code == 200

    # Only the bill's own "created" event exists - the windfall override
    # must not have produced a stray BillEvent.
    events = await _get_events(client, account["id"], bill["id"])
    assert [e["event_type"] for e in events] == ["created"]


async def test_events_pagination(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])
    for cents in range(160000, 160005):
        await client.patch(
            f"/api/v1/accounts/{account['id']}/bills/{bill['id']}", json={"amount_cents": cents}
        )

    res = await client.get(
        f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/events?limit=2&offset=0"
    )
    body = res.json()
    assert body["total"] == 6  # 1 created + 5 updates
    assert len(body["events"]) == 2


async def test_events_scoped_to_owning_user(client: AsyncClient):
    account = await _create_account(client)
    bill = await _create_bill(client, account["id"])

    _login_as("auth0|someone-else")
    res = await client.get(f"/api/v1/accounts/{account['id']}/bills/{bill['id']}/events")
    assert res.status_code == 404
