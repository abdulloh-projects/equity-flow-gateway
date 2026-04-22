"""
Unit tests for StartupService.

Strategy
--------
* `grpc.insecure_channel` is patched so no real network call is made.
* `startup_pb2_grpc.StartupServiceStub` is patched so we control the stub
  that the service holds internally.
* Every public method is covered for the happy path and for the case where
  the gRPC stub raises an exception.
* datetime objects are verified at the call-site level (the endpoint layer
  converts ISO-strings to datetime before handing them to the service).
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Environment & path bootstrap (must happen before any app import)
# ---------------------------------------------------------------------------
os.environ.setdefault("AUTH_URL", "localhost:50051")
os.environ.setdefault("STARTUP_URL", "localhost:50052")
os.environ.setdefault("ORIGINS", "http://localhost:3000")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SERVICE_MODULE = "apps.services.startup_service"

FOUNDED_AT = datetime(2021, 6, 15)
DEADLINE = datetime(2025, 12, 31, 23, 59, 59)


def _build_service_with_mock_stub():
    """
    Instantiate StartupService with both grpc.insecure_channel and the gRPC
    stub class patched out.  Returns (service_instance, mock_stub_instance).
    """
    mock_stub_instance = MagicMock()

    with (
        patch(f"{SERVICE_MODULE}.grpc.insecure_channel", return_value=MagicMock()),
        patch(
            f"{SERVICE_MODULE}.startup_pb2_grpc.StartupServiceStub",
            return_value=mock_stub_instance,
        ),
    ):
        from apps.services.startup_service import StartupService

        svc = StartupService()

    return svc, mock_stub_instance


# ===========================================================================
# Startup
# ===========================================================================


class TestCreateStartup:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.CreateStartup.return_value = expected

        result = svc.create_startup(
            user_id=42,
            name="GreenTech",
            location="Tashkent",
            description="Sustainable energy",
            website_url="https://greentech.uz",
            team_size=10,
            category_id=3,
            stage_id=1,
            founded_at=FOUNDED_AT,
        )

        assert result is expected

    def test_calls_stub_with_correct_request_fields(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.CreateStartupRequest") as mock_req:
            svc.create_startup(
                user_id=42,
                name="GreenTech",
                location="Tashkent",
                description="Sustainable energy",
                website_url="https://greentech.uz",
                team_size=10,
                category_id=3,
                stage_id=1,
                founded_at=FOUNDED_AT,
            )

        mock_req.assert_called_once_with(
            user_id=42,
            name="GreenTech",
            location="Tashkent",
            description="Sustainable energy",
            website_url="https://greentech.uz",
            team_size=10,
            category_id=3,
            stage_id=1,
            founded_at=FOUNDED_AT,
        )

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.CreateStartup.side_effect = RuntimeError("gRPC unavailable")

        with pytest.raises(RuntimeError, match="gRPC unavailable"):
            svc.create_startup(
                user_id=1,
                name="X",
                location="Y",
                description="Z",
                website_url="http://x.com",
                team_size=1,
                category_id=1,
                stage_id=1,
                founded_at=FOUNDED_AT,
            )


class TestUpdateStartup:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.UpdateStartup.return_value = expected

        result = svc.update_startup(
            startup_id=7,
            name="GreenTech Ltd",
            location="Tashkent",
            description="Updated",
            website_url="https://greentech.uz",
            category_id=3,
            stage_id=2,
            founded_at=FOUNDED_AT,
        )

        assert result is expected

    def test_calls_stub_with_correct_startup_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.UpdateStartupRequest") as mock_req:
            svc.update_startup(
                startup_id=7,
                name="GreenTech Ltd",
                location="Tashkent",
                description="Updated",
                website_url="https://greentech.uz",
                category_id=3,
                stage_id=2,
                founded_at=FOUNDED_AT,
            )

        mock_req.assert_called_once_with(
            startup_id=7,
            name="GreenTech Ltd",
            location="Tashkent",
            description="Updated",
            website_url="https://greentech.uz",
            category_id=3,
            stage_id=2,
            founded_at=FOUNDED_AT,
        )

    def test_update_with_none_founded_at(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.UpdateStartupRequest") as mock_req:
            svc.update_startup(
                startup_id=7,
                name="GreenTech Ltd",
                location="Tashkent",
                description="Updated",
                website_url="https://greentech.uz",
                category_id=3,
                stage_id=2,
                founded_at=None,
            )

        kwargs = mock_req.call_args.kwargs
        assert kwargs["founded_at"] is None

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.UpdateStartup.side_effect = RuntimeError("startup not found")

        with pytest.raises(RuntimeError, match="startup not found"):
            svc.update_startup(
                startup_id=999,
                name="X",
                location="Y",
                description="Z",
                website_url="http://x.com",
                category_id=1,
                stage_id=1,
                founded_at=None,
            )


class TestDeleteStartup:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.DeleteStartup.return_value = expected

        result = svc.delete_startup(startup_id=7)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.DeleteStartupRequest") as mock_req:
            svc.delete_startup(startup_id=7)

        mock_req.assert_called_once_with(startup_id=7)
        stub.DeleteStartup.assert_called_once()

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.DeleteStartup.side_effect = RuntimeError("record locked")

        with pytest.raises(RuntimeError, match="record locked"):
            svc.delete_startup(startup_id=7)


class TestGetStartup:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.GetStartup.return_value = expected

        result = svc.get_startup(startup_id=7)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.GetStartupRequest") as mock_req:
            svc.get_startup(startup_id=7)

        mock_req.assert_called_once_with(startup_id=7)
        stub.GetStartup.assert_called_once()

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.GetStartup.side_effect = RuntimeError("not found")

        with pytest.raises(RuntimeError, match="not found"):
            svc.get_startup(startup_id=999)


# ===========================================================================
# Campaign (Compaigns)
# ===========================================================================

CAMPAIGN_FIELDS = dict(
    startup_id=7,
    target_amount=500_000.0,
    min_investment=1_000.0,
    revenue=80_000.0,
    revenue_share=15.0,
    burn_rate=12_000.0,
    runway=18.0,
    active_customers=250.0,
    valuation=3_000_000.0,
    gross_margin=60.0,
    status="OPEN",
    deadline=DEADLINE,
)

UPDATE_CAMPAIGN_FIELDS = dict(
    campaign_id=12,
    target_amount=600_000.0,
    min_investment=2_000.0,
    revenue=90_000.0,
    revenue_share=20.0,
    burn_rate=11_000.0,
    runway=24.0,
    active_customers=300.0,
    valuation=4_000_000.0,
    gross_margin=65.0,
    status="OPEN",
    deadline=DEADLINE,
)


class TestCreateCampaign:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.CreateCompaigns.return_value = expected

        result = svc.create_compaigns(**CAMPAIGN_FIELDS)

        assert result is expected

    def test_calls_stub_with_correct_fields(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.CreateCompaignsRequest") as mock_req:
            svc.create_compaigns(**CAMPAIGN_FIELDS)

        mock_req.assert_called_once_with(**CAMPAIGN_FIELDS)
        stub.CreateCompaigns.assert_called_once()

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.CreateCompaigns.side_effect = RuntimeError("startup not found")

        with pytest.raises(RuntimeError, match="startup not found"):
            svc.create_compaigns(**CAMPAIGN_FIELDS)


class TestUpdateCampaign:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.UpdateCompaigns.return_value = expected

        result = svc.update_compaigns(**UPDATE_CAMPAIGN_FIELDS)

        assert result is expected

    def test_calls_stub_with_correct_campaign_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.UpdateCompaignsRequest") as mock_req:
            svc.update_compaigns(**UPDATE_CAMPAIGN_FIELDS)

        kwargs = mock_req.call_args.kwargs
        assert kwargs["campaign_id"] == 12

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.UpdateCompaigns.side_effect = RuntimeError("campaign not found")

        with pytest.raises(RuntimeError, match="campaign not found"):
            svc.update_compaigns(**UPDATE_CAMPAIGN_FIELDS)


class TestDeleteCampaign:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.DeleteCompaigns.return_value = expected

        result = svc.delete_compaigns(campaign_id=12)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.DeleteCompaignsRequest") as mock_req:
            svc.delete_compaigns(campaign_id=12)

        mock_req.assert_called_once_with(campaign_id=12)

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.DeleteCompaigns.side_effect = RuntimeError("error")

        with pytest.raises(RuntimeError):
            svc.delete_compaigns(campaign_id=12)


class TestGetCampaign:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.GetCompaigns.return_value = expected

        result = svc.get_compaigns(campaign_id=12)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.GetCompaignsRequest") as mock_req:
            svc.get_compaigns(campaign_id=12)

        mock_req.assert_called_once_with(campaign_id=12)

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.GetCompaigns.side_effect = RuntimeError("not found")

        with pytest.raises(RuntimeError, match="not found"):
            svc.get_compaigns(campaign_id=999)


# ===========================================================================
# Bank Info
# ===========================================================================

BANK_INFO_FIELDS = dict(
    startup_id=7,
    mfo="00873",
    account_number="20208000205738291001",
    receipant_name="GreenTech LLC",
)

UPDATE_BANK_INFO_FIELDS = dict(
    bank_info_id=3,
    mfo="00874",
    account_number="20208000205738291002",
    receipant_name="GreenTech Holdings",
)


class TestCreateBankInfo:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.CreateBankInfo.return_value = expected

        result = svc.create_bank_info(**BANK_INFO_FIELDS)

        assert result is expected

    def test_calls_stub_with_correct_fields(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.CreateBankInfoRequest") as mock_req:
            svc.create_bank_info(**BANK_INFO_FIELDS)

        mock_req.assert_called_once_with(**BANK_INFO_FIELDS)
        stub.CreateBankInfo.assert_called_once()

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.CreateBankInfo.side_effect = RuntimeError("duplicate bank info")

        with pytest.raises(RuntimeError, match="duplicate bank info"):
            svc.create_bank_info(**BANK_INFO_FIELDS)


class TestUpdateBankInfo:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.UpdateBankInfo.return_value = expected

        result = svc.update_bank_info(**UPDATE_BANK_INFO_FIELDS)

        assert result is expected

    def test_calls_stub_with_correct_bank_info_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.UpdateBankInfoRequest") as mock_req:
            svc.update_bank_info(**UPDATE_BANK_INFO_FIELDS)

        kwargs = mock_req.call_args.kwargs
        assert kwargs["bank_info_id"] == 3
        assert kwargs["mfo"] == "00874"
        assert kwargs["receipant_name"] == "GreenTech Holdings"

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.UpdateBankInfo.side_effect = RuntimeError("record not found")

        with pytest.raises(RuntimeError, match="record not found"):
            svc.update_bank_info(**UPDATE_BANK_INFO_FIELDS)


class TestDeleteBankInfo:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.DeleteBankInfo.return_value = expected

        result = svc.delete_bank_info(bank_info_id=3)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.DeleteBankInfoRequest") as mock_req:
            svc.delete_bank_info(bank_info_id=3)

        mock_req.assert_called_once_with(bank_info_id=3)

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.DeleteBankInfo.side_effect = RuntimeError("error")

        with pytest.raises(RuntimeError):
            svc.delete_bank_info(bank_info_id=3)


class TestGetBankInfo:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.GetBankInfo.return_value = expected

        result = svc.get_bank_info(bank_info_id=3)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(f"{SERVICE_MODULE}.startup_pb2.GetBankInfoRequest") as mock_req:
            svc.get_bank_info(bank_info_id=3)

        mock_req.assert_called_once_with(bank_info_id=3)

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.GetBankInfo.side_effect = RuntimeError("not found")

        with pytest.raises(RuntimeError, match="not found"):
            svc.get_bank_info(bank_info_id=999)


# ===========================================================================
# Campaign Update
# ===========================================================================


class TestCreateCampaignUpdate:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.CreateCompaignUpdate.return_value = expected

        result = svc.create_compaign_update(
            compaign_id=12,
            title="Milestone reached",
            body="We closed our seed round.",
        )

        assert result is expected

    def test_calls_stub_with_correct_fields(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(
            f"{SERVICE_MODULE}.startup_pb2.CreateCompaignUpdateRequest"
        ) as mock_req:
            svc.create_compaign_update(
                compaign_id=12,
                title="Milestone reached",
                body="We closed our seed round.",
            )

        mock_req.assert_called_once_with(
            compaign_id=12,
            title="Milestone reached",
            body="We closed our seed round.",
        )

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.CreateCompaignUpdate.side_effect = RuntimeError("campaign does not exist")

        with pytest.raises(RuntimeError, match="campaign does not exist"):
            svc.create_compaign_update(
                compaign_id=999,
                title="X",
                body="Y",
            )


class TestUpdateCampaignUpdate:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.UpdateCompaignUpdate.return_value = expected

        result = svc.update_compaign_update(
            update_id=5,
            title="Revised",
            body="Revised body.",
        )

        assert result is expected

    def test_calls_stub_with_correct_update_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(
            f"{SERVICE_MODULE}.startup_pb2.UpdateCompaignUpdateRequest"
        ) as mock_req:
            svc.update_compaign_update(
                update_id=5,
                title="Revised",
                body="Revised body.",
            )

        kwargs = mock_req.call_args.kwargs
        assert kwargs["update_id"] == 5
        assert kwargs["title"] == "Revised"

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.UpdateCompaignUpdate.side_effect = RuntimeError("update not found")

        with pytest.raises(RuntimeError, match="update not found"):
            svc.update_compaign_update(update_id=999, title="X", body="Y")


class TestDeleteCampaignUpdate:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.DeleteCompaignUpdate.return_value = expected

        result = svc.delete_compaign_update(update_id=5)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(
            f"{SERVICE_MODULE}.startup_pb2.DeleteCompaignUpdateRequest"
        ) as mock_req:
            svc.delete_compaign_update(update_id=5)

        mock_req.assert_called_once_with(update_id=5)

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.DeleteCompaignUpdate.side_effect = RuntimeError("error")

        with pytest.raises(RuntimeError):
            svc.delete_compaign_update(update_id=5)


class TestGetCampaignUpdate:
    def test_returns_stub_response(self):
        svc, stub = _build_service_with_mock_stub()
        expected = MagicMock()
        stub.GetCompaignUpdate.return_value = expected

        result = svc.get_compaign_update(update_id=5)

        assert result is expected

    def test_calls_stub_with_correct_id(self):
        svc, stub = _build_service_with_mock_stub()

        with patch(
            f"{SERVICE_MODULE}.startup_pb2.GetCompaignUpdateRequest"
        ) as mock_req:
            svc.get_compaign_update(update_id=5)

        mock_req.assert_called_once_with(update_id=5)

    def test_grpc_exception_propagates(self):
        svc, stub = _build_service_with_mock_stub()
        stub.GetCompaignUpdate.side_effect = RuntimeError("not found")

        with pytest.raises(RuntimeError, match="not found"):
            svc.get_compaign_update(update_id=999)


# ===========================================================================
# Constructor behaviour
# ===========================================================================


class TestStartupServiceConstructor:
    def test_creates_insecure_channel_with_startup_url(self):
        mock_channel = MagicMock()

        with (
            patch(
                f"{SERVICE_MODULE}.grpc.insecure_channel",
                return_value=mock_channel,
            ) as mock_channel_fn,
            patch(f"{SERVICE_MODULE}.startup_pb2_grpc.StartupServiceStub"),
        ):
            from apps.services.startup_service import StartupService

            StartupService()

        args, _ = mock_channel_fn.call_args
        assert args[0] == os.environ["STARTUP_URL"]

    def test_creates_stub_with_channel(self):
        mock_channel = MagicMock()

        with (
            patch(
                f"{SERVICE_MODULE}.grpc.insecure_channel",
                return_value=mock_channel,
            ),
            patch(
                f"{SERVICE_MODULE}.startup_pb2_grpc.StartupServiceStub"
            ) as mock_stub_cls,
        ):
            from apps.services.startup_service import StartupService

            StartupService()

        mock_stub_cls.assert_called_once_with(mock_channel)

    def test_channel_configured_with_round_robin_load_balancing(self):
        with (
            patch(
                f"{SERVICE_MODULE}.grpc.insecure_channel",
                return_value=MagicMock(),
            ) as mock_channel_fn,
            patch(f"{SERVICE_MODULE}.startup_pb2_grpc.StartupServiceStub"),
        ):
            from apps.services.startup_service import StartupService

            StartupService()

        _, kwargs = mock_channel_fn.call_args
        options = dict(kwargs.get("options", []))
        assert "grpc.service_config" in options
        assert "round_robin" in options["grpc.service_config"]
