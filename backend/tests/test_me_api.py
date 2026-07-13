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


async def test_consent_status_starts_unaccepted(client: AsyncClient):
    res = await client.get("/api/v1/me/consent")
    assert res.status_code == 200
    body = res.json()
    assert body["terms_accepted"] is False
    assert body["terms_accepted_at"] is None


async def test_accept_consent_sets_timestamp(client: AsyncClient):
    res = await client.post("/api/v1/me/consent")
    assert res.status_code == 200
    body = res.json()
    assert body["terms_accepted"] is True
    assert body["terms_accepted_at"] is not None

    res = await client.get("/api/v1/me/consent")
    assert res.json()["terms_accepted"] is True


async def test_accepting_twice_keeps_original_timestamp(client: AsyncClient):
    first = (await client.post("/api/v1/me/consent")).json()
    second = (await client.post("/api/v1/me/consent")).json()
    assert first["terms_accepted_at"] == second["terms_accepted_at"]


async def test_consent_scoped_to_current_user(client: AsyncClient):
    await client.post("/api/v1/me/consent")

    _login_as("auth0|someone-else")
    res = await client.get("/api/v1/me/consent")
    assert res.json()["terms_accepted"] is False
