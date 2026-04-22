"""
Unit tests for AuthService – the gRPC client wrapper.

Strategy
--------
* `grpc.insecure_channel` is patched so no real network connection is made.
* `auth_pb2_grpc.AuthServiceStub` is patched so we get a controllable stub.
* We verify:
    - the correct gRPC method is called
    - the correct request fields are forwarded
    - the response from the stub is returned as-is
    - gRPC errors propagate naturally (no silent swallowing)
"""

import os
import sys

os.environ.setdefault("AUTH_URL", "localhost:50051")
os.environ.setdefault("STARTUP_URL", "localhost:50052")
os.environ.setdefault("ORIGINS", "http://localhost:3000")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import MagicMock, call, patch  # noqa: E402

import grpc  # noqa: E402
import pytest  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SERVICE_PATH = "apps.services.auth_service"


def _build_service():
    """
    Return (AuthService instance, mock_stub) with gRPC fully patched out.

    The returned stub is the MagicMock that sits where AuthServiceStub would
    normally be, so you can configure return values and assert calls on it.
    """
    mock_channel = MagicMock()
    mock_stub = MagicMock()

    with (
        patch(f"{SERVICE_PATH}.grpc.insecure_channel", return_value=mock_channel),
        patch(f"{SERVICE_PATH}.auth_pb2_grpc.AuthServiceStub", return_value=mock_stub),
    ):
        from apps.services.auth_service import AuthService

        service = AuthService()

    return service, mock_stub


def _grpc_response(success: bool = True, message: str = "OK", **extra):
    """Build a lightweight mock that mimics a protobuf response message."""
    resp = MagicMock()
    resp.success = success
    resp.message = message
    for k, v in extra.items():
        setattr(resp, k, v)
    return resp


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestAuthServiceInit:
    def test_channel_is_created_with_auth_url(self):
        mock_channel = MagicMock()
        mock_stub = MagicMock()

        with (
            patch(
                f"{SERVICE_PATH}.grpc.insecure_channel", return_value=mock_channel
            ) as mock_chan,
            patch(
                f"{SERVICE_PATH}.auth_pb2_grpc.AuthServiceStub", return_value=mock_stub
            ),
        ):
            from apps.services.auth_service import AuthService

            AuthService()

        # The URL must match the env var we set at the top of this module
        call_args = mock_chan.call_args
        assert call_args[0][0] == "localhost:50051"

    def test_channel_uses_round_robin_load_balancing(self):
        mock_channel = MagicMock()
        mock_stub = MagicMock()

        with (
            patch(
                f"{SERVICE_PATH}.grpc.insecure_channel", return_value=mock_channel
            ) as mock_chan,
            patch(
                f"{SERVICE_PATH}.auth_pb2_grpc.AuthServiceStub", return_value=mock_stub
            ),
        ):
            from apps.services.auth_service import AuthService

            AuthService()

        options = dict(
            mock_chan.call_args[1].get(
                "options",
                mock_chan.call_args[0][1] if len(mock_chan.call_args[0]) > 1 else [],
            )
        )
        # The service_config key must be present somewhere in the options list
        all_options = mock_chan.call_args[1].get(
            "options",
            mock_chan.call_args[0][1] if len(mock_chan.call_args[0]) > 1 else [],
        )
        option_keys = [k for k, _ in all_options]
        assert "grpc.service_config" in option_keys

    def test_stub_is_created_with_channel(self):
        mock_channel = MagicMock()
        mock_stub = MagicMock()

        with (
            patch(f"{SERVICE_PATH}.grpc.insecure_channel", return_value=mock_channel),
            patch(
                f"{SERVICE_PATH}.auth_pb2_grpc.AuthServiceStub", return_value=mock_stub
            ) as mock_stub_cls,
        ):
            from apps.services.auth_service import AuthService

            AuthService()

        mock_stub_cls.assert_called_once_with(mock_channel)


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------


class TestAuthServiceRegister:
    def test_register_returns_stub_response(self):
        service, stub = _build_service()
        expected = _grpc_response(success=True, message="User registered")
        stub.Register.return_value = expected

        result = service.register(
            email="alice@example.com",
            password="pass123",
            first_name="Alice",
            last_name="Smith",
            role="INVESTOR",
        )

        assert result is expected

    def test_register_calls_stub_register_once(self):
        service, stub = _build_service()
        stub.Register.return_value = _grpc_response()

        service.register(
            email="alice@example.com",
            password="pass123",
            first_name="Alice",
            last_name="Smith",
            role="INVESTOR",
        )

        stub.Register.assert_called_once()

    def test_register_request_contains_correct_email(self):
        service, stub = _build_service()
        stub.Register.return_value = _grpc_response()

        service.register(
            email="alice@example.com",
            password="pass123",
            first_name="Alice",
            last_name="Smith",
            role="INVESTOR",
        )

        request_arg = stub.Register.call_args[0][0]
        assert request_arg.email == "alice@example.com"

    def test_register_request_contains_correct_name_fields(self):
        service, stub = _build_service()
        stub.Register.return_value = _grpc_response()

        service.register(
            email="bob@example.com",
            password="secret",
            first_name="Bob",
            last_name="Jones",
            role="INVESTOR",
        )

        request_arg = stub.Register.call_args[0][0]
        assert request_arg.first_name == "Bob"
        assert request_arg.last_name == "Jones"

    def test_register_request_contains_correct_password(self):
        service, stub = _build_service()
        stub.Register.return_value = _grpc_response()

        service.register(
            email="x@x.com",
            password="mypassword",
            first_name="X",
            last_name="Y",
            role="INVESTOR",
        )

        request_arg = stub.Register.call_args[0][0]
        assert request_arg.password == "mypassword"

    def test_register_failure_response_is_returned(self):
        service, stub = _build_service()
        stub.Register.return_value = _grpc_response(
            success=False, message="Email already in use"
        )

        result = service.register(
            email="dup@example.com",
            password="pass",
            first_name="A",
            last_name="B",
            role="INVESTOR",
        )

        assert result.success is False
        assert result.message == "Email already in use"

    def test_register_propagates_grpc_error(self):
        service, stub = _build_service()
        stub.Register.side_effect = grpc.RpcError("connection refused")

        with pytest.raises(grpc.RpcError):
            service.register(
                email="a@b.com",
                password="p",
                first_name="A",
                last_name="B",
                role="INVESTOR",
            )


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------


class TestAuthServiceLogin:
    def test_login_returns_stub_response(self):
        service, stub = _build_service()
        expected = _grpc_response(success=True, message="Login successful")
        stub.Login.return_value = expected

        result = service.login(email="alice@example.com", password="pass123")

        assert result is expected

    def test_login_calls_stub_login_once(self):
        service, stub = _build_service()
        stub.Login.return_value = _grpc_response()

        service.login(email="alice@example.com", password="pass123")

        stub.Login.assert_called_once()

    def test_login_request_contains_correct_email_and_password(self):
        service, stub = _build_service()
        stub.Login.return_value = _grpc_response()

        service.login(email="alice@example.com", password="mypass")

        request_arg = stub.Login.call_args[0][0]
        assert request_arg.email == "alice@example.com"
        assert request_arg.password == "mypass"

    def test_login_failure_response_is_returned(self):
        service, stub = _build_service()
        stub.Login.return_value = _grpc_response(
            success=False, message="Invalid credentials"
        )

        result = service.login(email="a@b.com", password="wrong")

        assert result.success is False
        assert result.message == "Invalid credentials"

    def test_login_propagates_grpc_error(self):
        service, stub = _build_service()
        stub.Login.side_effect = grpc.RpcError("unavailable")

        with pytest.raises(grpc.RpcError):
            service.login(email="a@b.com", password="pass")

    def test_login_does_not_call_other_stub_methods(self):
        service, stub = _build_service()
        stub.Login.return_value = _grpc_response()

        service.login(email="a@b.com", password="pass")

        stub.Register.assert_not_called()
        stub.SendOtp.assert_not_called()
        stub.VerifyOtp.assert_not_called()
        stub.DecodeToken.assert_not_called()


# ---------------------------------------------------------------------------
# send_otp()
# ---------------------------------------------------------------------------


class TestAuthServiceSendOtp:
    def test_send_otp_returns_stub_response(self):
        service, stub = _build_service()
        expected = _grpc_response(success=True, message="OTP sent")
        stub.SendOtp.return_value = expected

        result = service.send_otp(email="alice@example.com")

        assert result is expected

    def test_send_otp_calls_stub_send_otp_once(self):
        service, stub = _build_service()
        stub.SendOtp.return_value = _grpc_response()

        service.send_otp(email="alice@example.com")

        stub.SendOtp.assert_called_once()

    def test_send_otp_request_contains_correct_email(self):
        service, stub = _build_service()
        stub.SendOtp.return_value = _grpc_response()

        service.send_otp(email="alice@example.com")

        request_arg = stub.SendOtp.call_args[0][0]
        assert request_arg.email == "alice@example.com"

    def test_send_otp_failure_response_is_returned(self):
        service, stub = _build_service()
        stub.SendOtp.return_value = _grpc_response(
            success=False, message="No account with this email"
        )

        result = service.send_otp(email="unknown@example.com")

        assert result.success is False
        assert "No account" in result.message

    def test_send_otp_propagates_grpc_error(self):
        service, stub = _build_service()
        stub.SendOtp.side_effect = grpc.RpcError("deadline exceeded")

        with pytest.raises(grpc.RpcError):
            service.send_otp(email="a@b.com")

    def test_send_otp_does_not_call_other_stub_methods(self):
        service, stub = _build_service()
        stub.SendOtp.return_value = _grpc_response()

        service.send_otp(email="a@b.com")

        stub.Register.assert_not_called()
        stub.Login.assert_not_called()
        stub.VerifyOtp.assert_not_called()
        stub.DecodeToken.assert_not_called()


# ---------------------------------------------------------------------------
# verify_otp()
# ---------------------------------------------------------------------------


class TestAuthServiceVerifyOtp:
    def test_verify_otp_returns_stub_response(self):
        service, stub = _build_service()
        expected = _grpc_response(success=True, message="OTP verified")
        stub.VerifyOtp.return_value = expected

        result = service.verify_otp(email="alice@example.com", otp="482910")

        assert result is expected

    def test_verify_otp_calls_stub_verify_otp_once(self):
        service, stub = _build_service()
        stub.VerifyOtp.return_value = _grpc_response()

        service.verify_otp(email="alice@example.com", otp="111111")

        stub.VerifyOtp.assert_called_once()

    def test_verify_otp_request_contains_correct_email_and_otp(self):
        service, stub = _build_service()
        stub.VerifyOtp.return_value = _grpc_response()

        service.verify_otp(email="alice@example.com", otp="482910")

        request_arg = stub.VerifyOtp.call_args[0][0]
        assert request_arg.email == "alice@example.com"
        assert request_arg.otp == "482910"

    def test_verify_otp_failure_response_is_returned(self):
        service, stub = _build_service()
        stub.VerifyOtp.return_value = _grpc_response(
            success=False, message="Invalid or expired OTP"
        )

        result = service.verify_otp(email="a@b.com", otp="000000")

        assert result.success is False
        assert result.message == "Invalid or expired OTP"

    def test_verify_otp_propagates_grpc_error(self):
        service, stub = _build_service()
        stub.VerifyOtp.side_effect = grpc.RpcError("internal error")

        with pytest.raises(grpc.RpcError):
            service.verify_otp(email="a@b.com", otp="123456")

    def test_verify_otp_does_not_call_other_stub_methods(self):
        service, stub = _build_service()
        stub.VerifyOtp.return_value = _grpc_response()

        service.verify_otp(email="a@b.com", otp="000000")

        stub.Register.assert_not_called()
        stub.Login.assert_not_called()
        stub.SendOtp.assert_not_called()
        stub.DecodeToken.assert_not_called()


# ---------------------------------------------------------------------------
# decode_token()
# ---------------------------------------------------------------------------


class TestAuthServiceDecodeToken:
    def test_decode_token_returns_stub_response(self):
        service, stub = _build_service()
        expected = _grpc_response(success=True, message="Token decoded")
        stub.DecodeToken.return_value = expected

        result = service.decode_token(token="header.payload.signature")

        assert result is expected

    def test_decode_token_calls_stub_decode_token_once(self):
        service, stub = _build_service()
        stub.DecodeToken.return_value = _grpc_response()

        service.decode_token(token="some.jwt.token")

        stub.DecodeToken.assert_called_once()

    def test_decode_token_request_contains_correct_token(self):
        service, stub = _build_service()
        stub.DecodeToken.return_value = _grpc_response()

        service.decode_token(token="my.jwt.token")

        request_arg = stub.DecodeToken.call_args[0][0]
        assert request_arg.token == "my.jwt.token"

    def test_decode_token_invalid_token_returns_failure_response(self):
        service, stub = _build_service()
        stub.DecodeToken.return_value = _grpc_response(
            success=False, message="Token is expired"
        )

        result = service.decode_token(token="expired.token.here")

        assert result.success is False
        assert "expired" in result.message.lower()

    def test_decode_token_valid_token_returns_user_id_in_data(self):
        service, stub = _build_service()
        response = _grpc_response(success=True, message="OK")
        response.data = {"user_id": "42", "email": "alice@example.com"}
        stub.DecodeToken.return_value = response

        result = service.decode_token(token="valid.token.here")

        assert result.success is True
        assert result.data["user_id"] == "42"

    def test_decode_token_propagates_grpc_error(self):
        service, stub = _build_service()
        stub.DecodeToken.side_effect = grpc.RpcError("unauthenticated")

        with pytest.raises(grpc.RpcError):
            service.decode_token(token="bad.token")

    def test_decode_token_does_not_call_other_stub_methods(self):
        service, stub = _build_service()
        stub.DecodeToken.return_value = _grpc_response()

        service.decode_token(token="t")

        stub.Register.assert_not_called()
        stub.Login.assert_not_called()
        stub.SendOtp.assert_not_called()
        stub.VerifyOtp.assert_not_called()

    def test_decode_token_called_multiple_times_each_invocation_is_independent(self):
        service, stub = _build_service()
        stub.DecodeToken.side_effect = [
            _grpc_response(success=True, message="first"),
            _grpc_response(success=False, message="second"),
        ]

        r1 = service.decode_token(token="token-one")
        r2 = service.decode_token(token="token-two")

        assert r1.success is True
        assert r2.success is False
        assert stub.DecodeToken.call_count == 2
