"""Google Play subscription receipt verification.

Uses the Google Play Developer API (androidpublisher v3) to verify
subscription purchase tokens.

Requires GOOGLE_PLAY_CREDENTIALS_JSON env var pointing to a service
account JSON file with androidpublisher scope.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

PACKAGE_NAME = "com.vedantu.kiwimath"

_ANDROIDPUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
_SUBSCRIPTIONS_V2_URL = (
    "https://androidpublisher.googleapis.com/androidpublisher/v3"
    "/applications/{package_name}/purchases/subscriptionsv2/tokens/{token}"
)
_PRODUCTS_URL = (
    "https://androidpublisher.googleapis.com/androidpublisher/v3"
    "/applications/{package_name}/purchases/products/{product_id}"
    "/tokens/{token}"
)


def _get_credentials():
    """Load Google service account credentials from the env-configured JSON file.

    Returns None if GOOGLE_PLAY_CREDENTIALS_JSON is not set or the file
    cannot be loaded.
    """
    creds_path = os.environ.get("GOOGLE_PLAY_CREDENTIALS_JSON")
    if not creds_path:
        return None

    try:
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=[_ANDROIDPUBLISHER_SCOPE],
        )
        return credentials
    except Exception as exc:
        logger.error("Failed to load Google Play credentials from %s: %s", creds_path, exc)
        return None


def _make_authorized_request(url: str) -> Optional[Dict[str, Any]]:
    """Make an authorized GET request to the Google Play Developer API.

    Returns the parsed JSON response, or None on failure.
    """
    credentials = _get_credentials()
    if credentials is None:
        return None

    try:
        import httplib2
        from google.auth.transport.requests import AuthorizedSession
        import requests as _requests_mod

        session = AuthorizedSession(credentials)
        response = session.get(url, timeout=15)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Google Play API request failed: status=%d body=%s",
                response.status_code,
                response.text[:500],
            )
            return {"error": True, "status_code": response.status_code, "body": response.text[:500]}
    except ImportError:
        # Fall back to httplib2 if requests/AuthorizedSession is not available
        try:
            import httplib2
            from google.auth.transport._http_client import Request

            credentials.refresh(Request())
            http = httplib2.Http(timeout=15)
            headers = {}
            credentials.apply(headers)
            response, content = http.request(url, method="GET", headers=headers)

            status = int(response.get("status", 0))
            body = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content

            if status == 200:
                return json.loads(body)
            else:
                logger.error(
                    "Google Play API request failed (httplib2): status=%d body=%s",
                    status,
                    body[:500],
                )
                return {"error": True, "status_code": status, "body": body[:500]}
        except Exception as exc:
            logger.error("Google Play API request failed (httplib2 fallback): %s", exc)
            return {"error": True, "status_code": 0, "body": str(exc)}
    except Exception as exc:
        logger.error("Google Play API request failed: %s", exc)
        return {"error": True, "status_code": 0, "body": str(exc)}


def _verification_disabled_result() -> Dict[str, Any]:
    """Return a permissive result when verification is disabled (no credentials)."""
    logger.warning(
        "Google Play receipt verification is DISABLED — "
        "GOOGLE_PLAY_CREDENTIALS_JSON not set. Allowing purchase without verification."
    )
    return {
        "is_valid": True,
        "reason": "verification_disabled",
        "expiry_time": None,
        "auto_renewing": None,
        "payment_state": None,
    }


def verify_subscription(
    package_name: str,
    subscription_id: str,
    purchase_token: str,
) -> Dict[str, Any]:
    """Verify a Google Play subscription purchase token.

    Uses the androidpublisher.purchases.subscriptionsv2.get API to check
    whether the subscription is valid and active.

    Parameters
    ----------
    package_name : str
        Android package name (e.g. ``com.vedantu.kiwimath``).
    subscription_id : str
        The subscription product ID from the Play Console.
    purchase_token : str
        The purchase token provided by the client after a successful purchase.

    Returns
    -------
    dict
        Keys: is_valid (bool), expiry_time (str|None), auto_renewing (bool|None),
        payment_state (int|None), reason (str|None).
    """
    credentials = _get_credentials()
    if credentials is None:
        return _verification_disabled_result()

    url = _SUBSCRIPTIONS_V2_URL.format(
        package_name=package_name,
        token=purchase_token,
    )

    data = _make_authorized_request(url)

    if data is None:
        return _verification_disabled_result()

    if data.get("error"):
        return {
            "is_valid": False,
            "reason": f"api_error:{data.get('status_code')}",
            "expiry_time": None,
            "auto_renewing": None,
            "payment_state": None,
        }

    # subscriptionsv2.get returns fields like:
    #   subscriptionState: "SUBSCRIPTION_STATE_ACTIVE" | "SUBSCRIPTION_STATE_EXPIRED" | ...
    #   lineItems[].expiryTime, lineItems[].autoRenewingPlan
    subscription_state = data.get("subscriptionState", "")
    is_active = subscription_state in (
        "SUBSCRIPTION_STATE_ACTIVE",
        "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
    )

    # Extract expiry from the first line item
    expiry_time = None
    auto_renewing = None
    line_items = data.get("lineItems", [])
    if line_items:
        first_item = line_items[0]
        expiry_time = first_item.get("expiryTime")
        auto_renewing_plan = first_item.get("autoRenewingPlan", {})
        auto_renewing = auto_renewing_plan.get("autoRenewEnabled", False)

    # Check if subscription is expired by time
    if expiry_time and is_active:
        try:
            expiry_dt = datetime.fromisoformat(expiry_time.replace("Z", "+00:00"))
            if expiry_dt < datetime.now(timezone.utc):
                is_active = False
        except (ValueError, TypeError):
            pass

    payment_state = None
    latest_order = data.get("latestOrderId")

    return {
        "is_valid": is_active,
        "reason": f"state:{subscription_state}" if not is_active else None,
        "expiry_time": expiry_time,
        "auto_renewing": auto_renewing,
        "payment_state": payment_state,
        "subscription_state": subscription_state,
        "latest_order_id": latest_order,
    }


def verify_one_time_purchase(
    package_name: str,
    product_id: str,
    purchase_token: str,
) -> Dict[str, Any]:
    """Verify a Google Play one-time (in-app) purchase token.

    Used for Kiwi Coin packs and other consumable/non-consumable products.

    Parameters
    ----------
    package_name : str
        Android package name (e.g. ``com.vedantu.kiwimath``).
    product_id : str
        The in-app product ID from the Play Console.
    purchase_token : str
        The purchase token provided by the client.

    Returns
    -------
    dict
        Keys: is_valid (bool), purchase_state (int|None),
        consumption_state (int|None), reason (str|None).
    """
    credentials = _get_credentials()
    if credentials is None:
        return _verification_disabled_result()

    url = _PRODUCTS_URL.format(
        package_name=package_name,
        product_id=product_id,
        token=purchase_token,
    )

    data = _make_authorized_request(url)

    if data is None:
        return _verification_disabled_result()

    if data.get("error"):
        return {
            "is_valid": False,
            "reason": f"api_error:{data.get('status_code')}",
            "purchase_state": None,
            "consumption_state": None,
        }

    # purchaseState: 0 = Purchased, 1 = Canceled, 2 = Pending
    purchase_state = data.get("purchaseState", -1)
    consumption_state = data.get("consumptionState", -1)

    is_valid = purchase_state == 0  # Purchased

    return {
        "is_valid": is_valid,
        "reason": f"purchase_state:{purchase_state}" if not is_valid else None,
        "purchase_state": purchase_state,
        "consumption_state": consumption_state,
        "purchase_time_millis": data.get("purchaseTimeMillis"),
        "order_id": data.get("orderId"),
    }
