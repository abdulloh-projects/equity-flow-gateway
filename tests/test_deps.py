"""
Unit tests for the `get_current_user` FastAPI dependency (apps/api/deps.py).

Test matrix
-----------
Direct (pure-unit) tests – call `get_current_user` with mock credentials:
  * Valid JWT   → returns the user_id string from the decoded token
  * Expired/bad JWT → raises HTTP 401 with the expected detail message
  * AuthService.decode_token is called with the exact bearer token string

HTTP-stack tests – hit a real protected endpoint via httpx:
  * No Authorization header        → 403  (HTTPBearer auto_error)
  * Malformed header (no "Bearer") → 403
  * Valid header, valid token      → 200
  * Valid header, invalid token    → 401
"""

import os
import sys

# ── env vars before any app import ─────────────────────────────────────────
os.environ.setdefault("AUTH_URL", "localhost:50051")
os.environ.setdefault("STARTUP_URL", "localhost:50052")
os.environ.setdefault("ORIGINS", "http://localhost:3000")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import MagicMock, patch  # noqa: E402

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

DEPS_MODULE = "apps.api.deps"


# ── shared app fixture ──────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def app():
    from apps.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── helpers ─────────────────────────────────────────────────────────────────
def _make_credentials(token: str) -> HTTPAuthorizationCredentials:
    """Build an HTTPAuthorizationCredentials object with the given bearer token."""
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _mock_auth_service(success: bool = True, user_id: str = "42"):
    """
    Return a mock AuthService whose decode_token() returns a configurable stub.
    """
    response = MagicMock()
    response.success = success
    response.data = {"user_id": user_id} if success else {}

    service = MagicMock()
    service.decode_token.return_value = response
    return service


# ===========================================================================
# Direct / unit tests  (no HTTP layer)
# ===========================================================================


class TestGetCurrentUserDirect:
    """Call get_current_user() directly, bypassing HTTPBearer."""

    def _invoke(self, token: str, service):
        from apps.api.deps import get_current_user

        credentials = _make_credentials(token)
        with patch(f"{DEPS_MODULE}.AuthService", return_value=service):
            return get_current_user(credentials=credentials)

    # ── success path ────────────────────────────────────────────────────────

    def test_valid_token_returns_user_id(self):
        service = _mock_auth_service(success=True, user_id="99")
        result = self._invoke("valid.jwt.token", service)
        assert result == "99"

    def test_valid_token_returns_exact_user_id_from_response(self):
        service = _mock_auth_service(success=True, user_id="1234")
        result = self._invoke("some.token", service)
        assert result == "1234"

    def test_decode_token_is_called_with_the_bearer_token(self):
        token = "header.payload.signature"
        service = _mock_auth_service(success=True, user_id="7")
        self._invoke(token, service)
        service.decode_token.assert_called_once_with(token=token)

    def test_decode_token_is_called_exactly_once_per_request(self):
        service = _mock_auth_service(success=True, user_id="7")
        self._invoke("some.token", service)
        assert service.decode_token.call_count == 1

    def test_auth_service_is_instantiated_once_per_call(self):
        mock_cls = MagicMock(return_value=_mock_auth_service(success=True, user_id="7"))
        credentials = _make_credentials("token")

        from apps.api.deps import get_current_user

        with patch(f"{DEPS_MODULE}.AuthService", mock_cls):
            get_current_user(credentials=credentials)

        mock_cls.assert_called_once()

    # ── failure path ─────────────────────────────────────────────────────────

    def test_invalid_token_raises_401(self):
        service = _mock_auth_service(success=False)

        with pytest.raises(HTTPException) as exc_info:
            self._invoke("bad.token", service)

        assert exc_info.value.status_code == 401

    def test_invalid_token_detail_message(self):
        service = _mock_auth_service(success=False)

        with pytest.raises(HTTPException) as exc_info:
            self._invoke("bad.token", service)

        assert exc_info.value.detail == "Invalid or expired token"

    def test_expired_token_raises_401(self):
        """Same failure path – the service decides the token is expired."""
        service = _mock_auth_service(success=False)

        with pytest.raises(HTTPException) as exc_info:
            self._invoke("expired.jwt.token", service)

        assert exc_info.value.status_code == 401

    def test_empty_string_token_raises_401_when_service_rejects_it(self):
        service = _mock_auth_service(success=False)

        with pytest.raises(HTTPException) as exc_info:
            self._invoke("", service)

        assert exc_info.value.status_code == 401

    def test_different_token_strings_are_forwarded_correctly(self):
        """Ensure the raw bearer value is forwarded verbatim to the service."""
        for token in ["abc", "x.y.z", "Bearer should.not.be.double.wrapped"]:
            service = _mock_auth_service(success=True, user_id="1")
            self._invoke(token, service)
            service.decode_token.assert_called_with(token=token)


# ===========================================================================
# HTTP-stack tests  (full ASGI request cycle)
# ===========================================================================


class TestGetCurrentUserHTTP:
    """
    Exercise `get_current_user` through real HTTP requests to a protected
    endpoint.  We use the startup GET endpoint as the protected target because
    it only needs a valid user_id and a mocked StartupService.
    """

    STARTUP_MODULE = "apps.api.endpoints.startup"

    def _startup_patch(self):
        """Context manager that patches StartupService for the GET endpoint."""
        svc = MagicMock()
        svc.get_startup.return_value = MagicMock()
        return patch(f"{self.STARTUP_MODULE}.StartupService", return_value=svc), patch(
            f"{self.STARTUP_MODULE}.MessageToDict", return_value={"success": True}
        )

    # ── missing / malformed Authorization header ─────────────────────────────

    async def test_no_auth_header_returns_401(self, client):
        svc_patch, dict_patch = self._startup_patch()
        with svc_patch, dict_patch:
            response = await client.get("/api/startup/1")
        assert response.status_code == 401

    async def test_wrong_scheme_returns_401(self, client):
        """HTTPBearer rejects anything that is not a 'Bearer' scheme."""
        svc_patch, dict_patch = self._startup_patch()
        with svc_patch, dict_patch:
            response = await client.get(
                "/api/startup/1", headers={"Authorization": "Basic dXNlcjpwYXNz"}
            )
        assert response.status_code == 401

    async def test_malformed_header_value_returns_401(self, client):
        svc_patch, dict_patch = self._startup_patch()
        with svc_patch, dict_patch:
            response = await client.get(
                "/api/startup/1", headers={"Authorization": "not-a-valid-scheme"}
            )
        assert response.status_code == 401

    # ── invalid token ────────────────────────────────────────────────────────

    async def test_invalid_bearer_token_returns_401(self, client):
        invalid_service = _mock_auth_service(success=False)
        svc_patch, dict_patch = self._startup_patch()

        with (
            patch(f"{DEPS_MODULE}.AuthService", return_value=invalid_service),
            svc_patch,
            dict_patch,
        ):
            response = await client.get(
                "/api/startup/1",
                headers={"Authorization": "Bearer invalid.token.here"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired token"

    async def test_expired_bearer_token_returns_401(self, client):
        expired_service = _mock_auth_service(success=False)
        svc_patch, dict_patch = self._startup_patch()

        with (
            patch(f"{DEPS_MODULE}.AuthService", return_value=expired_service),
            svc_patch,
            dict_patch,
        ):
            response = await client.get(
                "/api/startup/1",
                headers={"Authorization": "Bearer expired.jwt.token"},
            )

        assert response.status_code == 401

    # ── valid token ──────────────────────────────────────────────────────────

    async def test_valid_bearer_token_allows_access(self, client):
        valid_service = _mock_auth_service(success=True, user_id="42")
        svc_patch, dict_patch = self._startup_patch()

        with (
            patch(f"{DEPS_MODULE}.AuthService", return_value=valid_service),
            svc_patch,
            dict_patch,
        ):
            response = await client.get(
                "/api/startup/1",
                headers={"Authorization": "Bearer valid.jwt.token"},
            )

        assert response.status_code == 200

    async def test_valid_token_decode_is_called_with_bearer_value(self, client):
        """Verify the raw token string (without 'Bearer ') reaches decode_token."""
        token_value = "the.actual.jwt.payload"
        valid_service = _mock_auth_service(success=True, user_id="7")
        svc_patch, dict_patch = self._startup_patch()

        with (
            patch(f"{DEPS_MODULE}.AuthService", return_value=valid_service),
            svc_patch,
            dict_patch,
        ):
            await client.get(
                "/api/startup/1",
                headers={"Authorization": f"Bearer {token_value}"},
            )

        valid_service.decode_token.assert_called_once_with(token=token_value)

    async def test_valid_token_propagates_user_id_to_endpoint(self, client):
        """
        The user_id returned by get_current_user must reach the endpoint handler.
        We verify this indirectly: create_startup converts user_id to int(user_id)
        and passes it to the service.
        """
        user_id = "55"
        valid_service = _mock_auth_service(success=True, user_id=user_id)

        create_svc = MagicMock()
        create_svc.create_startup.return_value = MagicMock()

        with (
            patch(f"{DEPS_MODULE}.AuthService", return_value=valid_service),
            patch("apps.api.endpoints.startup.StartupService", return_value=create_svc),
            patch(
                "apps.api.endpoints.startup.MessageToDict",
                return_value={"success": True},
            ),
        ):
            await client.post(
                "/api/startup/create",
                json={
                    "name": "TestCo",
                    "description": "desc",
                    "location": "NYC",
                    "website_url": "https://test.co",
                    "team_size": 5,
                    "category_id": 1,
                    "stage_id": 1,
                    "founded_at": "2022-01-01T00:00:00",
                },
                headers={"Authorization": f"Bearer some.token"},
            )

        call_kwargs = create_svc.create_startup.call_args.kwargs
        assert call_kwargs["user_id"] == int(user_id)
