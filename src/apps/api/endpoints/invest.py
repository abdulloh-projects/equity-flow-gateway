import logging
from typing import Optional

from apps.api.deps import get_current_user
from apps.services.startup_service import StartupService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invest", tags=["invest"])


class InvestRequest(BaseModel):
    startup_id: int = Field(...)
    campaign_id: int = Field(...)
    amount: float = Field(..., gt=0)
    message: Optional[str] = None


class InvestResponse(BaseModel):
    success: bool
    message: str
    investment_id: Optional[str] = None


class MyInvestmentsResponse(BaseModel):
    success: bool
    investments: list = []


@router.post("/", response_model=InvestResponse)
async def invest(
    request: InvestRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        result = StartupService().record_investment(
            investor_id=user_id,
            startup_id=request.startup_id,
            campaign_id=request.campaign_id,
            amount=request.amount,
            message=request.message,
        )
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        logger.info("Investment %s: user=%s startup=%d amount=%.2f", result.investment_id, user_id, request.startup_id, request.amount)
        return InvestResponse(success=True, message=result.message, investment_id=result.investment_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Invest error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/my", response_model=MyInvestmentsResponse)
async def my_investments(user_id: str = Depends(get_current_user)):
    try:
        result = StartupService().get_investments_by_user(user_id=user_id)
        investments = [
            {
                "id": inv.id,
                "user_id": inv.investor_id,
                "startup_id": inv.startup_id,
                "campaign_id": inv.campaign_id,
                "amount": inv.amount,
                "message": inv.message,
                "status": inv.status,
                "created_at": inv.created_at.ToJsonString() if inv.HasField("created_at") else "",
            }
            for inv in result.investments
        ]
        return MyInvestmentsResponse(success=True, investments=investments)
    except Exception as exc:
        logger.exception("Get investments error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/by-startup/{startup_id}")
async def investments_by_startup(
    startup_id: int,
    user_id: str = Depends(get_current_user),
):
    try:
        result = StartupService().get_investments_by_startup(startup_id=startup_id)
        investments = [
            {
                "id": inv.id,
                "user_id": inv.investor_id,
                "startup_id": inv.startup_id,
                "campaign_id": inv.campaign_id,
                "amount": inv.amount,
                "message": inv.message,
                "status": inv.status,
                "created_at": inv.created_at.ToJsonString() if inv.HasField("created_at") else "",
            }
            for inv in result.investments
        ]
        return {"success": True, "investments": investments}
    except Exception as exc:
        logger.exception("Get investments by startup error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
