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

ROLE_MAP = {"INVESTOR": "INVESTOR", "FOUNDER": "STARTUPPER", "ADMIN": "ADMIN"}
ROLE_REVERSE_MAP = {"investor": "INVESTOR", "startupper": "FOUNDER", "admin": "ADMIN", "0": "INVESTOR", "1": "ADMIN", "2": "FOUNDER"}


@router.post("/register")
async def register(data: RegisterSchema):
    auth_service = AuthService()
    mapped_role = ROLE_MAP.get(data.role, data.role)
    res = auth_service.register(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        role=mapped_role,
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

    result = MessageToDict(res)
    data_dict = result.get("data", {})

    access_token = data_dict.get("accessToken", "")
    result["token"] = access_token

    if access_token:
        try:
            decode_res = auth_service.decode_token(token=access_token)
            if decode_res.success:
                decoded_role = decode_res.data.get("role", "")
                data_dict["role"] = ROLE_REVERSE_MAP.get(decoded_role, decoded_role)
        except Exception:
            data_dict["role"] = ""

    data_dict["userId"] = data_dict.get("userId", data_dict.get("user_id", ""))
    result["data"] = data_dict

    return result


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
