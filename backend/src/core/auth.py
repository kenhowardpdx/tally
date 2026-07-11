import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from src.core.config import settings

security = HTTPBearer()

_jwks_cache: dict | None = None


def _get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache
    if _jwks_cache is None or force_refresh:
        # Explicit and tighter than httpx's 5s default - this blocks every
        # cold-cache request, so a slow/unreachable Auth0 should fail fast
        # rather than tie up the request for a library-default duration.
        response = httpx.get(
            f"https://{settings.auth0_domain}/.well-known/jwks.json", timeout=3.0
        )
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


def _fetch_jwks_or_503(force_refresh: bool = False) -> dict:
    # A JWKS fetch failure (Auth0 outage, network issue, or AUTH0_DOMAIN unset/
    # misconfigured producing an invalid URL) is an upstream/config problem, not
    # something the caller's token could ever be valid or invalid against - so
    # it gets its own status code rather than looking like a 401 auth failure.
    try:
        return _get_jwks(force_refresh=force_refresh)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to reach Auth0 to validate the token",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    jwks = _fetch_jwks_or_503()
    try:
        return _decode(token, jwks)
    except (ExpiredSignatureError, JWTClaimsError) as exc:
        # Not a key problem (expired token / wrong audience or issuer) - a
        # fresh JWKS wouldn't change the outcome, so don't bother refetching.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    except JWTError:
        # jose wraps a signature-verification failure (jws.verify's JWSError)
        # into a plain JWTError - that's the case a stale JWKS actually causes,
        # e.g. an Auth0 signing-key rotation since our cache was populated.
        # Refetch once before giving up, rather than 401ing every request
        # until this process/container recycles.
        jwks = _fetch_jwks_or_503(force_refresh=True)
        try:
            return _decode(token, jwks)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            ) from exc
