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


class CreateCompaignRequest(BaseModel):
    startup_id: int = Field(...)
    target_amount: int = Field(...)
    min_investment: int = Field(...)
    revenue: int = Field(...)
    revenue_share: int = Field(...)
    burn_rate: int = Field(...)
    runway: int = Field(...)
    active_customers: int = Field(...)
    evaluation: int = Field(...)
    gross_margin: int = Field(...)
    status: str = Field(...)
    deadline: str = Field(...)


class CreateBankInfoRequest(BaseModel):
    startup_id: int = Field(...)
    mfo: str = Field(...)
    account_number: str = Field(...)
    receipant_name: str = Field(...)


class CreateCompaignUpdateRequest(BaseModel):
    compaign_id: int = Field(...)
    title: str = Field(...)
    body: str = Field(...)
