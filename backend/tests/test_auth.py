import time

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwk, jwt

from src.core import auth
from src.core.config import settings


def _generate_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def _jwks_for(public_pem: bytes) -> dict:
    return {"keys": [jwk.construct(public_pem, algorithm="RS256").to_dict()]}


@pytest.fixture
def rsa_keypair():
    return _generate_keypair()


def _make_token(private_pem: bytes, **claim_overrides) -> str:
    claims = {
        "sub": "auth0|123",
        "email": "user@example.com",
        "aud": settings.auth0_audience,
        "iss": f"https://{settings.auth0_domain}/",
        "exp": time.time() + 60,
    }
    claims.update(claim_overrides)
    return jwt.encode(claims, private_pem, algorithm="RS256")


def test_get_current_user_bypasses_validation_when_dev_auth_bypass_is_set(monkeypatch):
    monkeypatch.setattr(settings, "dev_auth_bypass", True)

    payload = auth.get_current_user(None)

    assert payload["sub"] == "auth0|charlie_kelly_dev"
    assert payload["email"] == "charlie.kelly@paddys.bar"


def test_get_current_user_rejects_missing_credentials_with_401():
    # HTTPBearer(auto_error=False) passes None here when the Authorization
    # header is absent - get_current_user must handle that itself rather than
    # crashing on credentials.credentials (AttributeError -> 500) or relying
    # on HTTPBearer's default auto_error behavior (which raises 403, not 401).
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(None)
    assert exc_info.value.status_code == 401


def test_get_current_user_accepts_valid_token(monkeypatch, rsa_keypair):
    private_pem, public_pem = rsa_keypair
    monkeypatch.setattr(auth, "_get_jwks", lambda force_refresh=False: _jwks_for(public_pem))

    token = _make_token(private_pem)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    payload = auth.get_current_user(credentials)

    assert payload["sub"] == "auth0|123"
    assert payload["email"] == "user@example.com"


def test_get_current_user_rejects_wrong_audience_without_refetching_jwks(monkeypatch, rsa_keypair):
    private_pem, public_pem = rsa_keypair
    calls = []

    def fake_get_jwks(force_refresh: bool = False) -> dict:
        calls.append(force_refresh)
        return _jwks_for(public_pem)

    monkeypatch.setattr(auth, "_get_jwks", fake_get_jwks)

    token = _make_token(private_pem, aud="someone-elses-api")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(credentials)
    assert exc_info.value.status_code == 401
    # A wrong audience isn't a stale-JWKS problem - a refetch wouldn't help,
    # so get_current_user shouldn't waste a request on one.
    assert calls == [False]


def test_get_current_user_rejects_expired_token_without_refetching_jwks(monkeypatch, rsa_keypair):
    private_pem, public_pem = rsa_keypair
    calls = []

    def fake_get_jwks(force_refresh: bool = False) -> dict:
        calls.append(force_refresh)
        return _jwks_for(public_pem)

    monkeypatch.setattr(auth, "_get_jwks", fake_get_jwks)

    token = _make_token(private_pem, exp=time.time() - 60)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(credentials)
    assert exc_info.value.status_code == 401
    assert calls == [False]


def test_get_current_user_rejects_token_signed_by_wrong_key(monkeypatch, rsa_keypair):
    _, public_pem = rsa_keypair
    other_private_pem, _ = _generate_keypair()
    monkeypatch.setattr(auth, "_get_jwks", lambda force_refresh=False: _jwks_for(public_pem))

    token = _make_token(other_private_pem)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(credentials)
    assert exc_info.value.status_code == 401


def test_get_current_user_returns_503_when_jwks_unreachable(monkeypatch, rsa_keypair):
    private_pem, _ = rsa_keypair

    def broken_get_jwks(force_refresh: bool = False) -> dict:
        raise httpx.ConnectError("could not reach auth0")

    monkeypatch.setattr(auth, "_get_jwks", broken_get_jwks)

    token = _make_token(private_pem)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(credentials)
    # An Auth0/JWKS outage is an upstream problem, not a client auth failure -
    # it shouldn't look like an invalid token (401).
    assert exc_info.value.status_code == 503


def test_get_current_user_refetches_jwks_once_on_stale_cache(monkeypatch, rsa_keypair):
    """A cached JWKS that predates an Auth0 key rotation shouldn't 401 forever -
    get_current_user should refetch once and succeed against the current key."""
    old_private_pem, old_public_pem = _generate_keypair()
    new_private_pem, new_public_pem = rsa_keypair

    def fake_get_jwks(force_refresh: bool = False) -> dict:
        return _jwks_for(new_public_pem if force_refresh else old_public_pem)

    monkeypatch.setattr(auth, "_get_jwks", fake_get_jwks)

    token = _make_token(new_private_pem)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    payload = auth.get_current_user(credentials)

    assert payload["sub"] == "auth0|123"
