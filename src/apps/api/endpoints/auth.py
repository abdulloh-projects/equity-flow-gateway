from apps.schemas.auth_schema import (
    LoginSchema,
    RegisterSchema,
    SendOTPSchema,
    VerifyOTPSchema,
)
from apps.services.auth_service import AuthService
from fastapi import APIRouter, Depends, HTTPException
from google.protobuf.json_format import MessageToDict

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(data: RegisterSchema):
    auth_service = AuthService()
    res = auth_service.register(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return MessageToDict(res)


@router.post("/login")
async def login(data: LoginSchema):
    auth_service = AuthService()
    res = auth_service.login(
        email=data.email,
        password=data.password,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return MessageToDict(res)


@router.post("/send-otp")
async def send_otp(data: SendOTPSchema):
    auth_service = AuthService()
    res = auth_service.send_otp(
        email=data.email,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return MessageToDict(res)


@router.post("/verify-otp")
async def verify_otp(data: VerifyOTPSchema):
    auth_service = AuthService()
    res = auth_service.verify_otp(
        email=data.email,
        otp=data.otp,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return MessageToDict(res)
