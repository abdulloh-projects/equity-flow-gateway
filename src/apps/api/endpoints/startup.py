from datetime import datetime

from apps.api.deps import get_current_user
from apps.db import get_conn
from apps.schemas.startup_schema import (
    CreateBankInfoRequest,
    CreateCompaignsRequest,
    CreateCompaignUpdateRequest,
    CreateStartupRequest,
    DeleteBankInfoRequest,
    DeleteCompaignsRequest,
    DeleteCompaignUpdateRequest,
    DeleteStartupRequest,
    GetBankInfoRequest,
    GetCompaignsRequest,
    GetCompaignUpdateRequest,
    GetStartupRequest,
    UpdateBankInfoRequest,
    UpdateCompaignsRequest,
    UpdateCompaignUpdateRequest,
    UpdateStartupRequest,
)
from apps.services.startup_service import StartupService
from fastapi import APIRouter, Depends, HTTPException
from google.protobuf.json_format import MessageToDict

router = APIRouter(prefix="/startup", tags=["startup"])

_startup_bank_info: dict[int, int] = {}


@router.post("/create")
async def create_startup(
    request: CreateStartupRequest, user_id: str = Depends(get_current_user)
):
    try:
        startup = StartupService().create_startup(
            user_id=int(user_id),
            name=request.name,
            location=request.location,
            description=request.description,
            website_url=request.website_url,
            team_size=request.team_size,
            category_id=request.category_id,
            stage_id=request.stage_id,
            founded_at=datetime.fromisoformat(request.founded_at),
        )
        return MessageToDict(startup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update")
async def update_startup(
    request: UpdateStartupRequest, user_id: str = Depends(get_current_user)
):
    try:
        startup = StartupService().update_startup(
            startup_id=request.startup_id,
            name=request.name,
            location=request.location,
            description=request.description,
            website_url=request.website_url,
            category_id=request.category_id,
            stage_id=request.stage_id,
            founded_at=datetime.fromisoformat(request.founded_at)
            if request.founded_at
            else None,
        )
        return MessageToDict(startup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_startup(
    request: DeleteStartupRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().delete_startup(startup_id=request.startup_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compaign")
async def create_compaigns(
    request: CreateCompaignsRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().create_compaigns(
            startup_id=request.startup_id,
            target_amount=request.target_amount,
            min_investment=request.min_investment,
            revenue=request.revenue,
            revenue_share=request.revenue_share,
            burn_rate=request.burn_rate,
            runway=request.runway,
            active_customers=request.active_customers,
            valuation=request.valuation,
            gross_margin=request.gross_margin,
            status=request.status,
            deadline=datetime.fromisoformat(request.deadline),
        )
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/compaign/update")
async def update_compaigns(
    request: UpdateCompaignsRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().update_compaigns(
            campaign_id=request.campaign_id,
            target_amount=request.target_amount,
            min_investment=request.min_investment,
            revenue=request.revenue,
            revenue_share=request.revenue_share,
            burn_rate=request.burn_rate,
            runway=request.runway,
            active_customers=request.active_customers,
            valuation=request.valuation,
            gross_margin=request.gross_margin,
            status=request.status,
            deadline=datetime.fromisoformat(request.deadline)
            if request.deadline
            else None,
        )
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/compaign/delete")
async def delete_compaigns(
    request: DeleteCompaignsRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().delete_compaigns(campaign_id=request.campaign_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bank-info")
async def create_bank_info(
    request: CreateBankInfoRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().create_bank_info(
            startup_id=request.startup_id,
            mfo=request.mfo,
            account_number=request.account_number,
            receipant_name=request.receipant_name,
        )
        result_dict = MessageToDict(result)
        bank_info_id = result_dict.get("data", {}).get("bank_info_id")
        if bank_info_id:
            bid = int(bank_info_id)
            _startup_bank_info[request.startup_id] = bid
            with get_conn() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO startup_bank_info (startup_id, bank_info_id) VALUES (?, ?)",
                    (request.startup_id, bid),
                )
        return result_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bank-info/update")
async def update_bank_info(
    request: UpdateBankInfoRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().update_bank_info(
            bank_info_id=request.bank_info_id,
            mfo=request.mfo,
            account_number=request.account_number,
            receipant_name=request.receipant_name,
        )
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bank-info/delete")
async def delete_bank_info(
    request: DeleteBankInfoRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().delete_bank_info(bank_info_id=request.bank_info_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compaign-update")
async def create_compaign_update(
    request: CreateCompaignUpdateRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().create_compaign_update(
            compaign_id=request.compaign_id,
            title=request.title,
            body=request.body,
        )
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/compaign-update/update")
async def update_compaign_update(
    request: UpdateCompaignUpdateRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().update_compaign_update(
            update_id=request.update_id,
            title=request.title,
            body=request.body,
        )
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/compaign-update/delete")
async def delete_compaign_update(
    request: DeleteCompaignUpdateRequest, user_id: str = Depends(get_current_user)
):
    try:
        result = StartupService().delete_compaign_update(update_id=request.update_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    try:
        result = StartupService().list_categories()
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_startups(page: int = 1, limit: int = 9):
    try:
        result = StartupService().list_startups(page=page, limit=limit)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my")
async def get_my_startups(user_id: str = Depends(get_current_user)):
    try:
        result = StartupService().get_startups_by_user(user_id=int(user_id))
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{startup_id}/campaigns")
async def list_campaigns_by_startup(startup_id: int):
    try:
        result = StartupService().list_campaigns_by_startup(startup_id=startup_id)
        return MessageToDict(result, always_print_fields_with_no_presence=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{startup_id}")
async def get_startup(startup_id: int):
    try:
        result = StartupService().get_startup(startup_id=startup_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{startup_id}/bank-info")
async def get_bank_info_by_startup(
    startup_id: int, user_id: str = Depends(get_current_user)
):
    try:
        bank_info_id = _startup_bank_info.get(startup_id)
        if not bank_info_id:
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT bank_info_id FROM startup_bank_info WHERE startup_id = ?",
                    (startup_id,),
                ).fetchone()
                if row:
                    bank_info_id = row["bank_info_id"]
                    _startup_bank_info[startup_id] = bank_info_id
        if not bank_info_id:
            return {"success": False, "message": "No bank info found for this startup"}
        result = StartupService().get_bank_info(bank_info_id=bank_info_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compaign/{campaign_id}")
async def get_compaigns(campaign_id: int, user_id: str = Depends(get_current_user)):
    try:
        result = StartupService().get_compaigns(campaign_id=campaign_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bank-info/{bank_info_id}")
async def get_bank_info(bank_info_id: int, user_id: str = Depends(get_current_user)):
    try:
        result = StartupService().get_bank_info(bank_info_id=bank_info_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compaign-update/{update_id}")
async def get_compaign_update(update_id: int, user_id: str = Depends(get_current_user)):
    try:
        result = StartupService().get_compaign_update(update_id=update_id)
        return MessageToDict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
