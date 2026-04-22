"""
Tests for /api/auth/* endpoints.

Strategy
--------
* The gRPC layer is never touched.  We patch `AuthService` where it is
  *used* (inside the endpoint module) so the real constructor never runs.
* `MessageToDict` is also patched so we control the exact dict that gets
  serialised to JSON.
* Both the happy path and the failure path are exercised for every endpoint.
* Pydantic validation errors (422) are tested by sending incomplete bodies.
"""

import os
import sys

import pytest

os.environ.setdefault("AUTH_URL", "localhost:50051")
os.environ.setdefault("STARTUP_URL", "localhost:50052")
os.environ.setdefault("ORIGINS", "http://localhost:3000")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import MagicMock, patch

from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Shared app fixture
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUTH_MODULE = "apps.api.endpoints.auth"


def _make_mock_service(success: bool = True, message: str = "OK"):
    """Return a MagicMock whose methods return a consistent response stub."""
    stub = MagicMock()
    stub.success = success
    stub.message = message

    service = MagicMock()
    service.register.return_value = stub
    service.login.return_value = stub
    service.send_otp.return_value = stub
    service.verify_otp.return_value = stub
    service.decode_token.return_value = stub
    return service, stub


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------

REGISTER_PAYLOAD = {
    "email": "john@example.com",
    "password": "S3cr3tPass!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "INVESTOR",
}

REGISTER_RESPONSE_DICT = {
    "success": True,
    "message": "User registered successfully",
    "data": {
        "userId": "1",
        "email": "john@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "role": "INVESTOR",
    },
}


class TestRegisterEndpoint:
    async def test_register_success_returns_200(self, client):
        service, _ = _make_mock_service(
            success=True, message="User registered successfully"
        )

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value=REGISTER_RESPONSE_DICT),
        ):
            response = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "User registered successfully"
        assert body["data"]["email"] == "john@example.com"

    async def test_register_calls_service_with_correct_args(self, client):
        service, _ = _make_mock_service(success=True)

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value=REGISTER_RESPONSE_DICT),
        ):
            await client.post("/api/auth/register", json=REGISTER_PAYLOAD)

        service.register.assert_called_once_with(
            email="john@example.com",
            password="S3cr3tPass!",
            first_name="John",
            last_name="Doe",
            role="INVESTOR",
        )

    async def test_register_failure_returns_400(self, client):
        service, _ = _make_mock_service(
            success=False, message="Email already registered"
        )

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value={}),
        ):
            response = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    async def test_register_missing_email_returns_422(self, client):
        payload = {k: v for k, v in REGISTER_PAYLOAD.items() if k != "email"}

        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_missing_password_returns_422(self, client):
        payload = {k: v for k, v in REGISTER_PAYLOAD.items() if k != "password"}

        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_missing_role_returns_422(self, client):
        payload = {k: v for k, v in REGISTER_PAYLOAD.items() if k != "role"}

        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_empty_body_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/register", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

LOGIN_PAYLOAD = {
    "email": "john@example.com",
    "password": "S3cr3tPass!",
}

LOGIN_RESPONSE_DICT = {
    "success": True,
    "message": "Login successful",
    "data": {
        "userId": "1",
        "email": "john@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "accessToken": "header.payload.signature",
        "refreshToken": "refresh.token.value",
    },
}


class TestLoginEndpoint:
    async def test_login_success_returns_200(self, client):
        service, _ = _make_mock_service(success=True, message="Login successful")

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value=LOGIN_RESPONSE_DICT),
        ):
            response = await client.post("/api/auth/login", json=LOGIN_PAYLOAD)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]

    async def test_login_calls_service_with_correct_args(self, client):
        service, _ = _make_mock_service(success=True)

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value=LOGIN_RESPONSE_DICT),
        ):
            await client.post("/api/auth/login", json=LOGIN_PAYLOAD)

        service.login.assert_called_once_with(
            email="john@example.com",
            password="S3cr3tPass!",
        )

    async def test_login_wrong_credentials_returns_400(self, client):
        service, _ = _make_mock_service(
            success=False, message="Invalid email or password"
        )

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value={}),
        ):
            response = await client.post("/api/auth/login", json=LOGIN_PAYLOAD)

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid email or password"

    async def test_login_missing_email_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/login", json={"password": "pass"})

        assert response.status_code == 422

    async def test_login_missing_password_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/login", json={"email": "a@b.com"})

        assert response.status_code == 422

    async def test_login_empty_body_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/login", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/auth/send-otp
# ---------------------------------------------------------------------------

SEND_OTP_PAYLOAD = {"email": "john@example.com"}

SEND_OTP_RESPONSE_DICT = {
    "success": True,
    "message": "OTP sent to john@example.com",
}


class TestSendOTPEndpoint:
    async def test_send_otp_success_returns_200(self, client):
        service, _ = _make_mock_service(
            success=True, message="OTP sent to john@example.com"
        )

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value=SEND_OTP_RESPONSE_DICT),
        ):
            response = await client.post("/api/auth/send-otp", json=SEND_OTP_PAYLOAD)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "OTP" in body["message"]

    async def test_send_otp_calls_service_with_correct_email(self, client):
        service, _ = _make_mock_service(success=True)

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value=SEND_OTP_RESPONSE_DICT),
        ):
            await client.post("/api/auth/send-otp", json=SEND_OTP_PAYLOAD)

        service.send_otp.assert_called_once_with(email="john@example.com")

    async def test_send_otp_unknown_email_returns_400(self, client):
        service, _ = _make_mock_service(
            success=False, message="No account found for this email"
        )

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value={}),
        ):
            response = await client.post("/api/auth/send-otp", json=SEND_OTP_PAYLOAD)

        assert response.status_code == 400
        assert response.json()["detail"] == "No account found for this email"

    async def test_send_otp_missing_email_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/send-otp", json={})

        assert response.status_code == 422

    async def test_send_otp_service_is_instantiated_once_per_request(self, client):
        service, _ = _make_mock_service(success=True)
        mock_cls = MagicMock(return_value=service)

        with (
            patch(f"{AUTH_MODULE}.AuthService", mock_cls),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value=SEND_OTP_RESPONSE_DICT),
        ):
            await client.post("/api/auth/send-otp", json=SEND_OTP_PAYLOAD)

        mock_cls.assert_called_once()


# ---------------------------------------------------------------------------
# POST /api/auth/verify-otp
# ---------------------------------------------------------------------------

VERIFY_OTP_PAYLOAD = {"email": "john@example.com", "otp": "482910"}

VERIFY_OTP_RESPONSE_DICT = {
    "success": True,
    "message": "OTP verified",
}


class TestVerifyOTPEndpoint:
    async def test_verify_otp_success_returns_200(self, client):
        service, _ = _make_mock_service(success=True, message="OTP verified")

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(
                f"{AUTH_MODULE}.MessageToDict", return_value=VERIFY_OTP_RESPONSE_DICT
            ),
        ):
            response = await client.post(
                "/api/auth/verify-otp", json=VERIFY_OTP_PAYLOAD
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "OTP verified"

    async def test_verify_otp_calls_service_with_correct_args(self, client):
        service, _ = _make_mock_service(success=True)

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(
                f"{AUTH_MODULE}.MessageToDict", return_value=VERIFY_OTP_RESPONSE_DICT
            ),
        ):
            await client.post("/api/auth/verify-otp", json=VERIFY_OTP_PAYLOAD)

        service.verify_otp.assert_called_once_with(
            email="john@example.com",
            otp="482910",
        )

    async def test_verify_otp_wrong_code_returns_400(self, client):
        service, _ = _make_mock_service(success=False, message="Invalid or expired OTP")

        with (
            patch(f"{AUTH_MODULE}.AuthService", return_value=service),
            patch(f"{AUTH_MODULE}.MessageToDict", return_value={}),
        ):
            response = await client.post(
                "/api/auth/verify-otp", json=VERIFY_OTP_PAYLOAD
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid or expired OTP"

    async def test_verify_otp_missing_email_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/verify-otp", json={"otp": "123456"})

        assert response.status_code == 422

    async def test_verify_otp_missing_otp_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post(
                "/api/auth/verify-otp", json={"email": "john@example.com"}
            )

        assert response.status_code == 422

    async def test_verify_otp_empty_body_returns_422(self, client):
        with patch(f"{AUTH_MODULE}.AuthService"):
            response = await client.post("/api/auth/verify-otp", json={})

        assert response.status_code == 422
