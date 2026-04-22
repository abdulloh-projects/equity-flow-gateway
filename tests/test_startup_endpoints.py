"""
Tests for /api/startup/* endpoints.

Strategy
--------
* gRPC is never touched – StartupService is patched where it is *used*
  inside the endpoint module.
* MessageToDict is also patched so we own the dict that is returned as JSON.
* The `get_current_user` dependency is overridden via app.dependency_overrides
  so no real JWT / gRPC auth call is made.
* Every resource (Startup, Campaign, BankInfo, CampaignUpdate) has tests for:
    - success path  → 200
    - service raises an exception → 500
    - missing required body fields → 422  (Pydantic validation)
    - the service method is called with the correct arguments
"""

import os
import sys

os.environ.setdefault("AUTH_URL", "localhost:50051")
os.environ.setdefault("STARTUP_URL", "localhost:50052")
os.environ.setdefault("ORIGINS", "http://localhost:3000")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import MagicMock, patch  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

STARTUP_MODULE = "apps.api.endpoints.startup"

# ---------------------------------------------------------------------------
# Fixtures
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


@pytest.fixture(autouse=True)
def override_current_user(app):
    """
    Replace `get_current_user` with a lambda that returns a fixed user-id for
    every test in this module.  The override is cleaned up after each test.
    """
    from apps.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: "42"
    yield
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _service_mock(**method_results):
    """
    Build a MagicMock whose named methods return the given MagicMock responses.
    Any method not listed returns a generic success stub.
    """
    default = MagicMock()
    default.success = True
    default.message = "OK"

    svc = MagicMock()
    for method, result in method_results.items():
        getattr(svc, method).return_value = result

    # Unspecified methods fall back to `default`
    svc.configure_mock(
        **{
            f"{m}.return_value": default
            for m in [
                "create_startup",
                "update_startup",
                "delete_startup",
                "get_startup",
                "create_compaigns",
                "update_compaigns",
                "delete_compaigns",
                "get_compaigns",
                "create_bank_info",
                "update_bank_info",
                "delete_bank_info",
                "get_bank_info",
                "create_compaign_update",
                "update_compaign_update",
                "delete_compaign_update",
                "get_compaign_update",
            ]
            if m not in method_results
        }
    )
    return svc


def _ok_response(**extra):
    resp = MagicMock()
    resp.success = True
    resp.message = "OK"
    for k, v in extra.items():
        setattr(resp, k, v)
    return resp


# ===========================================================================
# STARTUP resource
# ===========================================================================

CREATE_STARTUP_PAYLOAD = {
    "name": "GreenTech",
    "description": "Sustainable energy startup",
    "location": "Tashkent",
    "website_url": "https://greentech.uz",
    "team_size": 12,
    "category_id": 3,
    "stage_id": 1,
    "founded_at": "2021-06-15T00:00:00",
}

CREATE_STARTUP_RESPONSE_DICT = {
    "success": True,
    "message": "Startup created",
    "startup": {
        "startupId": 7,
        "name": "GreenTech",
    },
}

UPDATE_STARTUP_PAYLOAD = {
    "startup_id": 7,
    "name": "GreenTech Ltd",
    "location": "Tashkent",
    "description": "Updated description",
    "website_url": "https://greentech.uz",
    "category_id": 3,
    "stage_id": 2,
    "founded_at": "2021-06-15T00:00:00",
}

DELETE_STARTUP_PAYLOAD = {"startup_id": 7}


class TestStartupCRUD:
    # ---- CREATE ------------------------------------------------------------

    async def test_create_startup_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_STARTUP_RESPONSE_DICT,
            ),
        ):
            response = await client.post(
                "/api/startup/create", json=CREATE_STARTUP_PAYLOAD
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["startup"]["startupId"] == 7

    async def test_create_startup_calls_service_with_correct_args(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_STARTUP_RESPONSE_DICT,
            ),
        ):
            await client.post("/api/startup/create", json=CREATE_STARTUP_PAYLOAD)

        call_kwargs = svc.create_startup.call_args.kwargs
        assert call_kwargs["user_id"] == 42  # int("42") from override
        assert call_kwargs["name"] == "GreenTech"
        assert call_kwargs["location"] == "Tashkent"
        assert call_kwargs["team_size"] == 12
        assert call_kwargs["category_id"] == 3

    async def test_create_startup_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.create_startup.side_effect = RuntimeError("gRPC connection failed")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.post(
                "/api/startup/create", json=CREATE_STARTUP_PAYLOAD
            )

        assert response.status_code == 500
        assert "gRPC connection failed" in response.json()["detail"]

    async def test_create_startup_missing_name_returns_422(self, client):
        payload = {k: v for k, v in CREATE_STARTUP_PAYLOAD.items() if k != "name"}
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/create", json=payload)
        assert response.status_code == 422

    async def test_create_startup_missing_founded_at_returns_422(self, client):
        payload = {k: v for k, v in CREATE_STARTUP_PAYLOAD.items() if k != "founded_at"}
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/create", json=payload)
        assert response.status_code == 422

    async def test_create_startup_empty_body_returns_422(self, client):
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/create", json={})
        assert response.status_code == 422

    # ---- UPDATE ------------------------------------------------------------

    async def test_update_startup_success(self, client):
        svc = _service_mock()
        update_dict = {"success": True, "message": "Startup updated"}
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value=update_dict),
        ):
            response = await client.put(
                "/api/startup/update", json=UPDATE_STARTUP_PAYLOAD
            )

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_update_startup_partial_fields(self, client):
        """Only startup_id is required; other fields are optional."""
        svc = _service_mock()
        partial = {"startup_id": 7, "name": "New Name"}
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.put("/api/startup/update", json=partial)

        assert response.status_code == 200

    async def test_update_startup_calls_service_with_correct_startup_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.put("/api/startup/update", json=UPDATE_STARTUP_PAYLOAD)

        call_kwargs = svc.update_startup.call_args.kwargs
        assert call_kwargs["startup_id"] == 7
        assert call_kwargs["name"] == "GreenTech Ltd"

    async def test_update_startup_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.update_startup.side_effect = RuntimeError("upstream error")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.put(
                "/api/startup/update", json=UPDATE_STARTUP_PAYLOAD
            )

        assert response.status_code == 500

    async def test_update_startup_missing_startup_id_returns_422(self, client):
        payload = {k: v for k, v in UPDATE_STARTUP_PAYLOAD.items() if k != "startup_id"}
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.put("/api/startup/update", json=payload)
        assert response.status_code == 422

    # ---- DELETE ------------------------------------------------------------

    async def test_delete_startup_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.request(
                "DELETE", "/api/startup/delete", json=DELETE_STARTUP_PAYLOAD
            )

        assert response.status_code == 200

    async def test_delete_startup_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.request(
                "DELETE", "/api/startup/delete", json=DELETE_STARTUP_PAYLOAD
            )

        svc.delete_startup.assert_called_once_with(startup_id=7)

    async def test_delete_startup_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.delete_startup.side_effect = RuntimeError("not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.request(
                "DELETE", "/api/startup/delete", json=DELETE_STARTUP_PAYLOAD
            )

        assert response.status_code == 500

    async def test_delete_startup_missing_startup_id_returns_422(self, client):
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.request("DELETE", "/api/startup/delete", json={})
        assert response.status_code == 422

    # ---- GET ---------------------------------------------------------------

    async def test_get_startup_success(self, client):
        svc = _service_mock()
        get_dict = {"success": True, "startup": {"startupId": 7, "name": "GreenTech"}}
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value=get_dict),
        ):
            response = await client.get("/api/startup/7")

        assert response.status_code == 200
        assert response.json()["startup"]["startupId"] == 7

    async def test_get_startup_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.get("/api/startup/7")

        svc.get_startup.assert_called_once_with(startup_id=7)

    async def test_get_startup_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.get_startup.side_effect = RuntimeError("startup not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.get("/api/startup/99")

        assert response.status_code == 500

    async def test_get_startup_non_integer_id_returns_422(self, client):
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.get("/api/startup/not-an-id")
        assert response.status_code == 422


# ===========================================================================
# CAMPAIGN resource
# ===========================================================================

CREATE_CAMPAIGN_PAYLOAD = {
    "startup_id": 7,
    "target_amount": 500000.0,
    "min_investment": 1000.0,
    "revenue": 80000.0,
    "revenue_share": 15.0,
    "burn_rate": 12000.0,
    "runway": 18.0,
    "active_customers": 250.0,
    "valuation": 3000000.0,
    "gross_margin": 60.0,
    "status": "OPEN",
    "deadline": "2025-12-31T23:59:59",
}

CREATE_CAMPAIGN_RESPONSE_DICT = {
    "success": True,
    "message": "Campaign created",
    "campaign": {"campaignId": 12, "startupId": 7},
}

UPDATE_CAMPAIGN_PAYLOAD = {
    "campaign_id": 12,
    "target_amount": 600000.0,
    "status": "OPEN",
    "deadline": "2025-12-31T23:59:59",
}

DELETE_CAMPAIGN_PAYLOAD = {"campaign_id": 12}


class TestCampaignCRUD:
    # ---- CREATE ------------------------------------------------------------

    async def test_create_campaign_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_CAMPAIGN_RESPONSE_DICT,
            ),
        ):
            response = await client.post(
                "/api/startup/compaign", json=CREATE_CAMPAIGN_PAYLOAD
            )

        assert response.status_code == 200
        body = response.json()
        assert body["campaign"]["campaignId"] == 12

    async def test_create_campaign_calls_service_with_correct_args(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_CAMPAIGN_RESPONSE_DICT,
            ),
        ):
            await client.post("/api/startup/compaign", json=CREATE_CAMPAIGN_PAYLOAD)

        kwargs = svc.create_compaigns.call_args.kwargs
        assert kwargs["startup_id"] == 7
        assert kwargs["target_amount"] == 500000.0
        assert kwargs["status"] == "OPEN"

    async def test_create_campaign_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.create_compaigns.side_effect = RuntimeError("startup not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.post(
                "/api/startup/compaign", json=CREATE_CAMPAIGN_PAYLOAD
            )

        assert response.status_code == 500
        assert "startup not found" in response.json()["detail"]

    async def test_create_campaign_missing_status_returns_422(self, client):
        payload = {k: v for k, v in CREATE_CAMPAIGN_PAYLOAD.items() if k != "status"}
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/compaign", json=payload)
        assert response.status_code == 422

    async def test_create_campaign_missing_deadline_returns_422(self, client):
        payload = {k: v for k, v in CREATE_CAMPAIGN_PAYLOAD.items() if k != "deadline"}
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/compaign", json=payload)
        assert response.status_code == 422

    async def test_create_campaign_optional_active_customers_can_be_omitted(
        self, client
    ):
        payload = {
            k: v for k, v in CREATE_CAMPAIGN_PAYLOAD.items() if k != "active_customers"
        }
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_CAMPAIGN_RESPONSE_DICT,
            ),
        ):
            response = await client.post("/api/startup/compaign", json=payload)

        assert response.status_code == 200

    # ---- UPDATE ------------------------------------------------------------

    async def test_update_campaign_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.put(
                "/api/startup/compaign/update", json=UPDATE_CAMPAIGN_PAYLOAD
            )

        assert response.status_code == 200

    async def test_update_campaign_calls_service_with_correct_campaign_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.put(
                "/api/startup/compaign/update", json=UPDATE_CAMPAIGN_PAYLOAD
            )

        kwargs = svc.update_compaigns.call_args.kwargs
        assert kwargs["campaign_id"] == 12
        assert kwargs["target_amount"] == 600000.0

    async def test_update_campaign_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.update_compaigns.side_effect = RuntimeError("campaign not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.put(
                "/api/startup/compaign/update", json=UPDATE_CAMPAIGN_PAYLOAD
            )

        assert response.status_code == 500

    async def test_update_campaign_missing_campaign_id_returns_422(self, client):
        payload = {
            k: v for k, v in UPDATE_CAMPAIGN_PAYLOAD.items() if k != "campaign_id"
        }
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.put("/api/startup/compaign/update", json=payload)
        assert response.status_code == 422

    # ---- DELETE ------------------------------------------------------------

    async def test_delete_campaign_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.request(
                "DELETE", "/api/startup/compaign/delete", json=DELETE_CAMPAIGN_PAYLOAD
            )

        assert response.status_code == 200

    async def test_delete_campaign_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.request(
                "DELETE", "/api/startup/compaign/delete", json=DELETE_CAMPAIGN_PAYLOAD
            )

        svc.delete_compaigns.assert_called_once_with(campaign_id=12)

    async def test_delete_campaign_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.delete_compaigns.side_effect = RuntimeError("error")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.request(
                "DELETE", "/api/startup/compaign/delete", json=DELETE_CAMPAIGN_PAYLOAD
            )

        assert response.status_code == 500

    async def test_delete_campaign_missing_campaign_id_returns_422(self, client):
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.request(
                "DELETE", "/api/startup/compaign/delete", json={}
            )
        assert response.status_code == 422

    # ---- GET ---------------------------------------------------------------

    async def test_get_campaign_success(self, client):
        svc = _service_mock()
        get_dict = {"success": True, "campaign": {"campaignId": 12}}
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value=get_dict),
        ):
            response = await client.get("/api/startup/compaign/12")

        assert response.status_code == 200
        assert response.json()["campaign"]["campaignId"] == 12

    async def test_get_campaign_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.get("/api/startup/compaign/12")

        svc.get_compaigns.assert_called_once_with(campaign_id=12)

    async def test_get_campaign_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.get_compaigns.side_effect = RuntimeError("not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.get("/api/startup/compaign/99")

        assert response.status_code == 500


# ===========================================================================
# BANK INFO resource
# ===========================================================================

CREATE_BANK_INFO_PAYLOAD = {
    "startup_id": 7,
    "mfo": "00873",
    "account_number": "20208000205738291001",
    "receipant_name": "GreenTech LLC",
}

CREATE_BANK_INFO_RESPONSE_DICT = {
    "success": True,
    "message": "Bank info created",
    "bankInfo": {"bankInfoId": 3, "startupId": 7},
}

UPDATE_BANK_INFO_PAYLOAD = {
    "bank_info_id": 3,
    "mfo": "00874",
    "account_number": "20208000205738291002",
    "receipant_name": "GreenTech Holdings",
}

DELETE_BANK_INFO_PAYLOAD = {"bank_info_id": 3}


class TestBankInfoCRUD:
    # ---- CREATE ------------------------------------------------------------

    async def test_create_bank_info_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_BANK_INFO_RESPONSE_DICT,
            ),
        ):
            response = await client.post(
                "/api/startup/bank-info", json=CREATE_BANK_INFO_PAYLOAD
            )

        assert response.status_code == 200
        body = response.json()
        assert body["bankInfo"]["bankInfoId"] == 3

    async def test_create_bank_info_calls_service_with_correct_args(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_BANK_INFO_RESPONSE_DICT,
            ),
        ):
            await client.post("/api/startup/bank-info", json=CREATE_BANK_INFO_PAYLOAD)

        kwargs = svc.create_bank_info.call_args.kwargs
        assert kwargs["startup_id"] == 7
        assert kwargs["mfo"] == "00873"
        assert kwargs["account_number"] == "20208000205738291001"
        assert kwargs["receipant_name"] == "GreenTech LLC"

    async def test_create_bank_info_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.create_bank_info.side_effect = RuntimeError("duplicate entry")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.post(
                "/api/startup/bank-info", json=CREATE_BANK_INFO_PAYLOAD
            )

        assert response.status_code == 500
        assert "duplicate entry" in response.json()["detail"]

    async def test_create_bank_info_missing_mfo_returns_422(self, client):
        payload = {k: v for k, v in CREATE_BANK_INFO_PAYLOAD.items() if k != "mfo"}
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/bank-info", json=payload)
        assert response.status_code == 422

    async def test_create_bank_info_missing_account_number_returns_422(self, client):
        payload = {
            k: v for k, v in CREATE_BANK_INFO_PAYLOAD.items() if k != "account_number"
        }
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/bank-info", json=payload)
        assert response.status_code == 422

    # ---- UPDATE ------------------------------------------------------------

    async def test_update_bank_info_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.put(
                "/api/startup/bank-info/update", json=UPDATE_BANK_INFO_PAYLOAD
            )

        assert response.status_code == 200

    async def test_update_bank_info_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.put(
                "/api/startup/bank-info/update", json=UPDATE_BANK_INFO_PAYLOAD
            )

        kwargs = svc.update_bank_info.call_args.kwargs
        assert kwargs["bank_info_id"] == 3
        assert kwargs["mfo"] == "00874"

    async def test_update_bank_info_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.update_bank_info.side_effect = RuntimeError("record not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.put(
                "/api/startup/bank-info/update", json=UPDATE_BANK_INFO_PAYLOAD
            )

        assert response.status_code == 500

    async def test_update_bank_info_missing_bank_info_id_returns_422(self, client):
        payload = {
            k: v for k, v in UPDATE_BANK_INFO_PAYLOAD.items() if k != "bank_info_id"
        }
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.put("/api/startup/bank-info/update", json=payload)
        assert response.status_code == 422

    async def test_update_bank_info_all_optional_fields_can_be_omitted(self, client):
        """Only bank_info_id is required for an update."""
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.put(
                "/api/startup/bank-info/update", json={"bank_info_id": 3}
            )

        assert response.status_code == 200

    # ---- DELETE ------------------------------------------------------------

    async def test_delete_bank_info_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.request(
                "DELETE", "/api/startup/bank-info/delete", json=DELETE_BANK_INFO_PAYLOAD
            )

        assert response.status_code == 200

    async def test_delete_bank_info_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.request(
                "DELETE", "/api/startup/bank-info/delete", json=DELETE_BANK_INFO_PAYLOAD
            )

        svc.delete_bank_info.assert_called_once_with(bank_info_id=3)

    async def test_delete_bank_info_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.delete_bank_info.side_effect = RuntimeError("error")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.request(
                "DELETE", "/api/startup/bank-info/delete", json=DELETE_BANK_INFO_PAYLOAD
            )

        assert response.status_code == 500

    # ---- GET ---------------------------------------------------------------

    async def test_get_bank_info_success(self, client):
        svc = _service_mock()
        get_dict = {"success": True, "bankInfo": {"bankInfoId": 3}}
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value=get_dict),
        ):
            response = await client.get("/api/startup/bank-info/3")

        assert response.status_code == 200
        assert response.json()["bankInfo"]["bankInfoId"] == 3

    async def test_get_bank_info_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.get("/api/startup/bank-info/3")

        svc.get_bank_info.assert_called_once_with(bank_info_id=3)

    async def test_get_bank_info_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.get_bank_info.side_effect = RuntimeError("not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.get("/api/startup/bank-info/99")

        assert response.status_code == 500


# ===========================================================================
# CAMPAIGN UPDATE resource
# ===========================================================================

CREATE_CAMPAIGN_UPDATE_PAYLOAD = {
    "compaign_id": 12,
    "title": "Milestone reached",
    "body": "We have successfully closed our seed round.",
}

CREATE_CAMPAIGN_UPDATE_RESPONSE_DICT = {
    "success": True,
    "message": "Update posted",
    "update": {"updateId": 5, "compaignId": 12},
}

UPDATE_CAMPAIGN_UPDATE_PAYLOAD = {
    "update_id": 5,
    "title": "Revised milestone",
    "body": "Updated body text.",
}

DELETE_CAMPAIGN_UPDATE_PAYLOAD = {"update_id": 5}


class TestCampaignUpdateCRUD:
    # ---- CREATE ------------------------------------------------------------

    async def test_create_campaign_update_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_CAMPAIGN_UPDATE_RESPONSE_DICT,
            ),
        ):
            response = await client.post(
                "/api/startup/compaign-update", json=CREATE_CAMPAIGN_UPDATE_PAYLOAD
            )

        assert response.status_code == 200
        body = response.json()
        assert body["update"]["updateId"] == 5

    async def test_create_campaign_update_calls_service_with_correct_args(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(
                f"{STARTUP_MODULE}.MessageToDict",
                return_value=CREATE_CAMPAIGN_UPDATE_RESPONSE_DICT,
            ),
        ):
            await client.post(
                "/api/startup/compaign-update", json=CREATE_CAMPAIGN_UPDATE_PAYLOAD
            )

        kwargs = svc.create_compaign_update.call_args.kwargs
        assert kwargs["compaign_id"] == 12
        assert kwargs["title"] == "Milestone reached"
        assert kwargs["body"] == "We have successfully closed our seed round."

    async def test_create_campaign_update_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.create_compaign_update.side_effect = RuntimeError("campaign does not exist")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.post(
                "/api/startup/compaign-update", json=CREATE_CAMPAIGN_UPDATE_PAYLOAD
            )

        assert response.status_code == 500
        assert "campaign does not exist" in response.json()["detail"]

    async def test_create_campaign_update_missing_title_returns_422(self, client):
        payload = {
            k: v for k, v in CREATE_CAMPAIGN_UPDATE_PAYLOAD.items() if k != "title"
        }
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/compaign-update", json=payload)
        assert response.status_code == 422

    async def test_create_campaign_update_missing_body_returns_422(self, client):
        payload = {
            k: v for k, v in CREATE_CAMPAIGN_UPDATE_PAYLOAD.items() if k != "body"
        }
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/compaign-update", json=payload)
        assert response.status_code == 422

    async def test_create_campaign_update_missing_campaign_id_returns_422(self, client):
        payload = {
            k: v
            for k, v in CREATE_CAMPAIGN_UPDATE_PAYLOAD.items()
            if k != "compaign_id"
        }
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.post("/api/startup/compaign-update", json=payload)
        assert response.status_code == 422

    # ---- UPDATE ------------------------------------------------------------

    async def test_update_campaign_update_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.put(
                "/api/startup/compaign-update/update",
                json=UPDATE_CAMPAIGN_UPDATE_PAYLOAD,
            )

        assert response.status_code == 200

    async def test_update_campaign_update_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.put(
                "/api/startup/compaign-update/update",
                json=UPDATE_CAMPAIGN_UPDATE_PAYLOAD,
            )

        kwargs = svc.update_compaign_update.call_args.kwargs
        assert kwargs["update_id"] == 5
        assert kwargs["title"] == "Revised milestone"

    async def test_update_campaign_update_partial_body_is_valid(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.put(
                "/api/startup/compaign-update/update",
                json={"update_id": 5, "title": "New title only"},
            )

        assert response.status_code == 200

    async def test_update_campaign_update_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.update_compaign_update.side_effect = RuntimeError("not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.put(
                "/api/startup/compaign-update/update",
                json=UPDATE_CAMPAIGN_UPDATE_PAYLOAD,
            )

        assert response.status_code == 500

    async def test_update_campaign_update_missing_update_id_returns_422(self, client):
        payload = {
            k: v for k, v in UPDATE_CAMPAIGN_UPDATE_PAYLOAD.items() if k != "update_id"
        }
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.put(
                "/api/startup/compaign-update/update", json=payload
            )
        assert response.status_code == 422

    # ---- DELETE ------------------------------------------------------------

    async def test_delete_campaign_update_success(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            response = await client.request(
                "DELETE",
                "/api/startup/compaign-update/delete",
                json=DELETE_CAMPAIGN_UPDATE_PAYLOAD,
            )

        assert response.status_code == 200

    async def test_delete_campaign_update_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.request(
                "DELETE",
                "/api/startup/compaign-update/delete",
                json=DELETE_CAMPAIGN_UPDATE_PAYLOAD,
            )

        svc.delete_compaign_update.assert_called_once_with(update_id=5)

    async def test_delete_campaign_update_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.delete_compaign_update.side_effect = RuntimeError("error")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.request(
                "DELETE",
                "/api/startup/compaign-update/delete",
                json=DELETE_CAMPAIGN_UPDATE_PAYLOAD,
            )

        assert response.status_code == 500

    async def test_delete_campaign_update_missing_update_id_returns_422(self, client):
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.request(
                "DELETE", "/api/startup/compaign-update/delete", json={}
            )
        assert response.status_code == 422

    # ---- GET ---------------------------------------------------------------

    async def test_get_campaign_update_success(self, client):
        svc = _service_mock()
        get_dict = {
            "success": True,
            "update": {"updateId": 5, "title": "Milestone reached"},
        }
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value=get_dict),
        ):
            response = await client.get("/api/startup/compaign-update/5")

        assert response.status_code == 200
        assert response.json()["update"]["updateId"] == 5

    async def test_get_campaign_update_calls_service_with_correct_id(self, client):
        svc = _service_mock()
        with (
            patch(f"{STARTUP_MODULE}.StartupService", return_value=svc),
            patch(f"{STARTUP_MODULE}.MessageToDict", return_value={"success": True}),
        ):
            await client.get("/api/startup/compaign-update/5")

        svc.get_compaign_update.assert_called_once_with(update_id=5)

    async def test_get_campaign_update_service_exception_returns_500(self, client):
        svc = MagicMock()
        svc.get_compaign_update.side_effect = RuntimeError("not found")

        with patch(f"{STARTUP_MODULE}.StartupService", return_value=svc):
            response = await client.get("/api/startup/compaign-update/99")

        assert response.status_code == 500

    async def test_get_campaign_update_non_integer_id_returns_422(self, client):
        with patch(f"{STARTUP_MODULE}.StartupService"):
            response = await client.get("/api/startup/compaign-update/bad-id")
        assert response.status_code == 422
