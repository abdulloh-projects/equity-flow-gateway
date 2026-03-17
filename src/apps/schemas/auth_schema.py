from pydantic import BaseModel, Field


class RegisterSchema(BaseModel):
    email: str = Field(...)
    password: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    role: str = Field(...)


class LoginSchema(BaseModel):
    email: str = Field(...)
    password: str = Field(...)


class SendOTPSchema(BaseModel):
    email: str = Field(...)


class VerifyOTPSchema(BaseModel):
    email: str = Field(...)
    otp: str = Field(...)
