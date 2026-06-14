"""
Firebase ID-token authentication for the Kiwimath API.

Usage:
    from app.core.auth import verify_token, verify_admin

    # Per-router (in main.py):
    app.include_router(user_router, dependencies=[Depends(verify_token)])
    app.include_router(admin_router, dependencies=[Depends(verify_admin)])

    # Per-endpoint identity enforcement:
    @router.get("/profile")
    def get_profile(user_id: str, decoded: dict = Depends(verify_token)):
        assert_user_match(decoded, user_id)
        ...

Environment variables:
    KIWIMATH_AUTH_DISABLED=1     → skip verification, return a dev identity
                                   (local dev / CI only — default OFF)
    KIWIMATH_ADMIN_EMAILS        → comma-separated admin email allowlist
    KIWIMATH_ADMIN_UIDS          → comma-separated admin Firebase UID allowlist
    KIWIMATH_INTERNAL_API_KEY    → shared secret for internal service calls
                                   (Cloud Scheduler) via X-Internal-Key header
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request

logger = logging.getLogger("kiwimath.auth")

# Identity returned when KIWIMATH_AUTH_DISABLED=1 (local dev / test suite).
_DEV_IDENTITY: Dict[str, Any] = {
    "uid": "dev-local",
    "email": "dev@kiwimath.local",
    "dev_mode": True,
}

# Identity for internal service calls authenticated via X-Internal-Key.
_INTERNAL_IDENTITY: Dict[str, Any] = {
    "uid": "internal-service",
    "email": "internal@kiwimath.local",
    "internal": True,
}


def _auth_disabled() -> bool:
    return os.environ.get("KIWIMATH_AUTH_DISABLED", "") == "1"


def _ensure_firebase_initialized() -> None:
    """Initialize firebase_admin once, reusing any existing default app.

    Import is lazy so the API can still start when firebase-admin is not
    installed locally (auth must then be disabled via KIWIMATH_AUTH_DISABLED).
    """
    import firebase_admin  # lazy — keep module importable without the package

    if not firebase_admin._apps:
        firebase_admin.initialize_app()


def internal_key_matches(provided: str) -> bool:
    """Constant-time comparison of a provided key against the internal secret.

    Returns False when the env var is unset/empty (fail closed).
    """
    expected = os.environ.get("KIWIMATH_INTERNAL_API_KEY", "")
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided, expected)


def _internal_request(request: Request) -> bool:
    # Header-only: the old `?api_key=` query fallback leaked the secret into
    # access logs. Cloud Scheduler sends X-Internal-Key (see clan_cron.yaml).
    provided = request.headers.get("X-Internal-Key") or ""
    return internal_key_matches(provided)


def verify_token(request: Request) -> Dict[str, Any]:
    """FastAPI dependency: verify the Firebase ID token in the Authorization header.

    Returns the decoded token (contains uid, email, etc.) and stashes the uid
    on request.state for downstream middleware/handlers. Raises 401 when the
    token is missing or invalid.
    """
    if _auth_disabled():
        decoded = dict(_DEV_IDENTITY)
        request.state.uid = decoded["uid"]
        request.state.decoded_token = decoded
        return decoded

    # Internal service calls (Cloud Scheduler cron) authenticate with the
    # shared internal key instead of a Firebase ID token.
    if _internal_request(request):
        decoded = dict(_INTERNAL_IDENTITY)
        request.state.uid = decoded["uid"]
        request.state.decoded_token = decoded
        return decoded

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header (expected 'Bearer <Firebase ID token>')",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header[len("Bearer "):].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Empty bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        _ensure_firebase_initialized()
        from firebase_admin import auth as fb_auth  # lazy import

        decoded = fb_auth.verify_id_token(token)
    except ImportError:
        logger.error("firebase-admin not installed — cannot verify ID tokens")
        raise HTTPException(status_code=401, detail="Authentication unavailable")
    except Exception as e:
        logger.warning(f"ID token verification failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.uid = decoded.get("uid")
    request.state.decoded_token = decoded
    return decoded


def _admin_allowlists() -> tuple:
    emails = {
        e.strip().lower()
        for e in os.environ.get("KIWIMATH_ADMIN_EMAILS", "").split(",")
        if e.strip()
    }
    uids = {
        u.strip()
        for u in os.environ.get("KIWIMATH_ADMIN_UIDS", "").split(",")
        if u.strip()
    }
    return emails, uids


def is_admin(decoded: Dict[str, Any]) -> bool:
    """Check a decoded token against the admin allowlists."""
    if decoded.get("dev_mode"):
        return True  # auth disabled — local dev / tests
    emails, uids = _admin_allowlists()
    email = (decoded.get("email") or "").lower()
    uid = decoded.get("uid") or ""
    return bool((email and email in emails) or (uid and uid in uids))


def verify_admin(decoded: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """FastAPI dependency: require an admin identity. 403 otherwise."""
    if not is_admin(decoded):
        raise HTTPException(status_code=403, detail="Admin access required")
    return decoded


def assert_user_match(decoded: Dict[str, Any], user_id: str) -> None:
    """Raise 403 unless the token uid matches the requested user_id.

    Admins, internal service calls, and dev mode are always allowed.
    Call this inside endpoints that accept a user_id/student_id parameter.
    """
    if decoded.get("dev_mode") or decoded.get("internal"):
        return
    if is_admin(decoded):
        return
    if user_id and decoded.get("uid") == user_id:
        return
    raise HTTPException(
        status_code=403,
        detail="Forbidden: user_id does not match authenticated user",
    )


def enforce_user_match(
    request: Request,
    decoded: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """FastAPI dependency: 403 when a user_id/student_id/uid query parameter
    does not match the authenticated uid (admins exempt).

    Useful for GET endpoints that take the user id as a query parameter.
    POST endpoints with the id in the body should call assert_user_match().
    """
    requested = (
        request.query_params.get("user_id")
        or request.query_params.get("student_id")
        or request.query_params.get("uid")
    )
    if requested:
        assert_user_match(decoded, requested)
    return decoded
