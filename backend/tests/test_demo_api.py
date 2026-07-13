from httpx import AsyncClient


def _bill(id: int, **overrides) -> dict:
    payload = {
        "id": id,
        "name": "Rent",
        "amount_cents": 150000,
        "recurrence_type": "monthly",
        "recurrence_config": {},
        "start_date": "2024-01-15",
    }
    payload.update(overrides)
    return payload


def _payload(**overrides) -> dict:
    payload = {
        "bills": [_bill(1)],
        "cycle_type": "monthly",
        "start_date": "2024-01-01",
        "end_date": "2024-02-29",
        "starting_balance_cents": 100000,
        "income_per_cycle_cents": 200000,
    }
    payload.update(overrides)
    return payload


async def test_demo_forecast_requires_no_auth(client: AsyncClient):
    # No app.dependency_overrides[get_current_user] set up in this test at
    # all, unlike every other endpoint's test module - a real request
    # without a token must still succeed.
    res = await client.post("/api/v1/demo/forecast", json=_payload())
    assert res.status_code == 200
    body = res.json()
    assert len(body["cycles"]) == 2
    assert body["cycles"][0]["bills"][0]["name"] == "Rent"
    # 100000 + 200000*2 - 150000*2
    assert body["ending_balance_cents"] == 200000


async def test_demo_forecast_never_touches_the_database(client: AsyncClient):
    # Same request twice - if it wrote anything, a unique-constraint or
    # id-collision error would surface on the second call.
    res1 = await client.post("/api/v1/demo/forecast", json=_payload())
    res2 = await client.post("/api/v1/demo/forecast", json=_payload())
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json() == res2.json()


async def test_demo_forecast_rejects_invalid_recurrence_config(client: AsyncClient):
    # Unlike the real bills API, DemoBill validates recurrence_config eagerly
    # at the schema level (no pre-existing DB rows to grandfather in) - a
    # demo forecast can never actually hit the engine's unscheduled_bills
    # path, so this is the only outcome to test for invalid config.
    res = await client.post(
        "/api/v1/demo/forecast",
        json=_payload(bills=[_bill(1, recurrence_type="semimonthly", recurrence_config={"days": [40]})]),
    )
    assert res.status_code == 422


async def test_demo_forecast_rejects_end_before_start(client: AsyncClient):
    res = await client.post(
        "/api/v1/demo/forecast", json=_payload(start_date="2024-02-01", end_date="2024-01-01")
    )
    assert res.status_code == 422


async def test_demo_forecast_rejects_too_many_bills(client: AsyncClient):
    bills = [_bill(i) for i in range(26)]
    res = await client.post("/api/v1/demo/forecast", json=_payload(bills=bills))
    assert res.status_code == 422


async def test_demo_forecast_rejects_oversized_date_range(client: AsyncClient):
    res = await client.post(
        "/api/v1/demo/forecast", json=_payload(start_date="2024-01-01", end_date="2026-01-01")
    )
    assert res.status_code == 422
