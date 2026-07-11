import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.core.config import settings

security = HTTPBearer()

_jwks_cache: dict | None = None


def _get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache
    if _jwks_cache is None or force_refresh:
        response = httpx.get(f"https://{settings.auth0_domain}/.well-known/jwks.json")
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def _decode(token: str, jwks: dict) -> dict:
    # Pass the whole JWKS - jose tries every key in it and picks the one whose
    # kid/signature matches, so there's no need to pre-select a key ourselves.
    return jwt.decode(
        token,
        jwks,
        algorithms=["RS256"],
        audience=settings.auth0_audience,
        issuer=f"https://{settings.auth0_domain}/",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        try:
            payload = _decode(token, _get_jwks())
        except JWTError:
            # Our cached JWKS may predate an Auth0 signing-key rotation - refetch
            # once before giving up, rather than 401ing every request until this
            # process/container recycles.
            payload = _decode(token, _get_jwks(force_refresh=True))
    except (JWTError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    return payload
