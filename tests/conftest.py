import os
import sys

# ---------------------------------------------------------------------------
# Environment variables MUST be set before any application code is imported,
# because decouple reads them at module-import time.
# ---------------------------------------------------------------------------
os.environ.setdefault("AUTH_URL", "localhost:50051")
os.environ.setdefault("STARTUP_URL", "localhost:50052")
os.environ.setdefault("ORIGINS", "http://localhost:3000")

# Make `src/` importable so that `from apps.xxx import yyy` works in tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import MagicMock  # noqa: E402 – after path setup

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402


# ---------------------------------------------------------------------------
# Application fixture (session-scoped – created once for the whole test run)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """Return the FastAPI application instance."""
    from apps.main import app as fastapi_app  # lazy import after env setup

    return fastapi_app


# ---------------------------------------------------------------------------
# Async HTTP client
# ---------------------------------------------------------------------------
@pytest.fixture
async def async_client(app):
    """
    Yield an httpx AsyncClient wired directly to the FastAPI ASGI app.
    No real network connection is made.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Auth dependency override
# ---------------------------------------------------------------------------
@pytest.fixture
def override_current_user(app):
    """
    Replace the `get_current_user` dependency with a stub that always returns
    a fixed user-id string.  The override is cleaned up after each test.
    """
    from apps.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: "42"
    yield "42"
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# Generic gRPC stub mocks (reusable across service unit tests)
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_auth_stub():
    """A bare MagicMock that stands in for an AuthServiceStub instance."""
    return MagicMock()


@pytest.fixture
def mock_startup_stub():
    """A bare MagicMock that stands in for a StartupServiceStub instance."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Helper – build a mock gRPC response with common fields
# ---------------------------------------------------------------------------
def make_grpc_response(success: bool = True, message: str = "OK", **extra):
    """
    Return a MagicMock that mimics a protobuf response message.

    Usage
    -----
    resp = make_grpc_response(success=True, message="registered")
    resp.data.user_id = "7"
    """
    resp = MagicMock()
    resp.success = success
    resp.message = message
    for attr, value in extra.items():
        setattr(resp, attr, value)
    return resp
