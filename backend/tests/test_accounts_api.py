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


async def test_list_accounts_starts_empty(client: AsyncClient):
    res = await client.get("/api/v1/accounts")
    assert res.status_code == 200
    assert res.json() == []


async def test_create_and_get_account(client: AsyncClient):
    res = await client.post("/api/v1/accounts", json={"name": "Checking", "institution": "Bank"})
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Checking"
    assert body["institution"] == "Bank"

    res = await client.get(f"/api/v1/accounts/{body['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == body["id"]


async def test_update_account(client: AsyncClient):
    created = (await client.post("/api/v1/accounts", json={"name": "Checking"})).json()

    res = await client.patch(f"/api/v1/accounts/{created['id']}", json={"name": "Savings"})
    assert res.status_code == 200
    assert res.json()["name"] == "Savings"


async def test_delete_account(client: AsyncClient):
    created = (await client.post("/api/v1/accounts", json={"name": "Checking"})).json()

    res = await client.delete(f"/api/v1/accounts/{created['id']}")
    assert res.status_code == 204

    res = await client.get(f"/api/v1/accounts/{created['id']}")
    assert res.status_code == 404


async def test_cannot_see_another_users_account(client: AsyncClient):
    created = (await client.post("/api/v1/accounts", json={"name": "Checking"})).json()

    _login_as("auth0|someone-else")
    res = await client.get(f"/api/v1/accounts/{created['id']}")
    assert res.status_code == 404

    res = await client.get("/api/v1/accounts")
    assert res.json() == []
