"""
Pytest configuration for the Kiwimath backend test suite.

Disables Firebase ID-token verification BEFORE the app is imported so the
existing tests (which use TestClient without Authorization headers) keep
working. Production deploys must NOT set KIWIMATH_AUTH_DISABLED.
"""

import os

os.environ.setdefault("KIWIMATH_AUTH_DISABLED", "1")
