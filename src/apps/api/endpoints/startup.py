from apps.schemas.startup_schema import (
    CreateBankInfoRequest,
    CreateCompaignRequest,
    CreateCompaignUpdateRequest,
    CreateStartupRequest,
)
from apps.services.startup_service import StartupService
from fastapi import APIRouter, Depends, HTTPException
from google.protobuf.json_format import MessageToDict

router = APIRouter(prefix="/startup", tags=["startup"])


@router.post("/create")
async def create_startup(request: CreateStartupRequest):
    try:
        startup = StartupService.create_startup(request)
        return MessageToDict(startup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def create_compaign_update(request: CreateCompaignUpdateRequest):
    try:
        startup = StartupService.create_compaign_update(request)
        return MessageToDict(startup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bank-info")
async def create_bank_info(request: CreateBankInfoRequest):
    try:
        startup = StartupService.create_bank_info(request)
        return MessageToDict(startup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compaign")
async def create_compaign(request: CreateCompaignRequest):
    try:
        startup = StartupService.create_compaign(request)
        return MessageToDict(startup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
