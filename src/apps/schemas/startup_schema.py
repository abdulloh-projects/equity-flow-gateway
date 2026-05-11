from typing import Optional

from pydantic import BaseModel, Field


class CreateStartupRequest(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    location: str = Field(...)
    website_url: str = Field(...)
    team_size: int = Field(...)
    category_id: int = Field(...)
    stage_id: int = Field(...)
    founded_at: str = Field(...)


class UpdateStartupRequest(BaseModel):
    startup_id: int = Field(...)
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    category_id: Optional[int] = None
    stage_id: Optional[int] = None
    founded_at: Optional[str] = None


class DeleteStartupRequest(BaseModel):
    startup_id: int = Field(...)


class CreateCompaignsRequest(BaseModel):
    startup_id: int = Field(...)
    target_amount: float = Field(...)
    min_investment: float = Field(...)
    revenue: float = Field(...)
    revenue_share: float = Field(...)
    burn_rate: float = Field(...)
    runway: float = Field(...)
    active_customers: Optional[float] = None
    valuation: float = Field(...)
    gross_margin: float = Field(...)
    status: str = Field(...)
    deadline: str = Field(...)


class UpdateCompaignsRequest(BaseModel):
    campaign_id: int = Field(...)
    target_amount: Optional[float] = None
    min_investment: Optional[float] = None
    revenue: Optional[float] = None
    revenue_share: Optional[float] = None
    burn_rate: Optional[float] = None
    runway: Optional[float] = None
    active_customers: Optional[float] = None
    valuation: Optional[float] = None
    gross_margin: Optional[float] = None
    status: Optional[str] = None
    deadline: Optional[str] = None


class DeleteCompaignsRequest(BaseModel):
    campaign_id: int = Field(...)


class CreateBankInfoRequest(BaseModel):
    startup_id: int = Field(...)
    mfo: str = Field(...)
    account_number: str = Field(...)
    receipant_name: str = Field(...)


class UpdateBankInfoRequest(BaseModel):
    bank_info_id: int = Field(...)
    mfo: Optional[str] = None
    account_number: Optional[str] = None
    receipant_name: Optional[str] = None


class DeleteBankInfoRequest(BaseModel):
    bank_info_id: int = Field(...)


class CreateCompaignUpdateRequest(BaseModel):
    compaign_id: int = Field(...)
    title: str = Field(...)
    body: str = Field(...)


class UpdateCompaignUpdateRequest(BaseModel):
    update_id: int = Field(...)
    title: Optional[str] = None
    body: Optional[str] = None


class DeleteCompaignUpdateRequest(BaseModel):
    update_id: int = Field(...)


class GetStartupRequest(BaseModel):
    startup_id: int = Field(...)


class GetCompaignsRequest(BaseModel):
    campaign_id: int = Field(...)


class GetBankInfoRequest(BaseModel):
    bank_info_id: int = Field(...)


class GetCompaignUpdateRequest(BaseModel):
    update_id: int = Field(...)


class ListStartupsRequest(BaseModel):
    page: int = 1
    limit: int = 9
    status: Optional[str] = None


class GetStartupsByUserRequest(BaseModel):
    user_id: int = Field(...)


class ListCampaignsByStartupRequest(BaseModel):
    startup_id: int = Field(...)
