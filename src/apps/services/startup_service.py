import json

import grpc
from apps.generated import startup_pb2, startup_pb2_grpc
from decouple import config


class StartupService:
    def __init__(self):
        service_config = json.dumps({"loadBalancingConfig": [{"round_robin": {}}]})
        startup_url = config("STARTUP_URL")
        self.channel = grpc.insecure_channel(
            startup_url, options=[("grpc.service_config", service_config)]
        )
        self.stub = startup_pb2_grpc.StartupServiceStub(self.channel)

    def create_startup(
        self,
        user_id,
        name,
        location,
        description,
        website_url,
        team_size,
        category_id,
        stage_id,
        founded_at,
    ):
        request = startup_pb2.CreateStartupRequest(
            user_id=user_id,
            name=name,
            location=location,
            description=description,
            website_url=website_url,
            team_size=team_size,
            category_id=category_id,
            stage_id=stage_id,
            founded_at=founded_at,
        )
        return self.stub.CreateStartup(request)

    def update_startup(
        self,
        startup_id,
        name,
        location,
        description,
        website_url,
        category_id,
        stage_id,
        founded_at,
    ):
        request = startup_pb2.UpdateStartupRequest(
            startup_id=startup_id,
            name=name,
            location=location,
            description=description,
            website_url=website_url,
            category_id=category_id,
            stage_id=stage_id,
            founded_at=founded_at,
        )
        return self.stub.UpdateStartup(request)

    def delete_startup(self, startup_id):
        request = startup_pb2.DeleteStartupRequest(startup_id=startup_id)
        return self.stub.DeleteStartup(request)

    def create_compaigns(
        self,
        startup_id,
        target_amount,
        min_investment,
        revenue,
        revenue_share,
        burn_rate,
        runway,
        active_customers,
        valuation,
        gross_margin,
        status,
        deadline,
    ):
        request = startup_pb2.CreateCompaignsRequest(
            startup_id=startup_id,
            target_amount=target_amount,
            min_investment=min_investment,
            revenue=revenue,
            revenue_share=revenue_share,
            burn_rate=burn_rate,
            runway=runway,
            active_customers=active_customers,
            valuation=valuation,
            gross_margin=gross_margin,
            status=status,
            deadline=deadline,
        )
        return self.stub.CreateCompaigns(request)

    def update_compaigns(
        self,
        campaign_id,
        target_amount=None,
        min_investment=None,
        revenue=None,
        revenue_share=None,
        burn_rate=None,
        runway=None,
        active_customers=None,
        valuation=None,
        gross_margin=None,
        status=None,
        deadline=None,
        raised_amount=None,
    ):
        kwargs = {"campaign_id": campaign_id}
        if target_amount is not None: kwargs["target_amount"] = target_amount
        if min_investment is not None: kwargs["min_investment"] = min_investment
        if revenue is not None: kwargs["revenue"] = revenue
        if revenue_share is not None: kwargs["revenue_share"] = revenue_share
        if burn_rate is not None: kwargs["burn_rate"] = burn_rate
        if runway is not None: kwargs["runway"] = runway
        if active_customers is not None: kwargs["active_customers"] = active_customers
        if valuation is not None: kwargs["valuation"] = valuation
        if gross_margin is not None: kwargs["gross_margin"] = gross_margin
        if status is not None: kwargs["status"] = status
        if deadline is not None: kwargs["deadline"] = deadline
        if raised_amount is not None: kwargs["raised_amount"] = raised_amount
        request = startup_pb2.UpdateCompaignsRequest(**kwargs)
        return self.stub.UpdateCompaigns(request)

    def record_investment(self, investor_id: str, startup_id: int, campaign_id: int, amount: float, message: str = None):
        kwargs = dict(investor_id=investor_id, startup_id=startup_id, campaign_id=campaign_id, amount=amount)
        if message:
            kwargs["message"] = message
        request = startup_pb2.RecordInvestmentRequest(**kwargs)
        return self.stub.RecordInvestment(request)

    def get_investments_by_user(self, user_id: str):
        request = startup_pb2.GetInvestmentsByUserRequest(user_id=user_id)
        return self.stub.GetInvestmentsByUser(request)

    def get_investments_by_startup(self, startup_id: int):
        request = startup_pb2.GetInvestmentsByStartupRequest(startup_id=startup_id)
        return self.stub.GetInvestmentsByStartup(request)

    def delete_compaigns(self, campaign_id):
        request = startup_pb2.DeleteCompaignsRequest(campaign_id=campaign_id)
        return self.stub.DeleteCompaigns(request)

    def create_bank_info(
        self,
        startup_id,
        mfo,
        account_number,
        receipant_name,
    ):
        request = startup_pb2.CreateBankInfoRequest(
            startup_id=startup_id,
            mfo=mfo,
            account_number=account_number,
            receipant_name=receipant_name,
        )
        return self.stub.CreateBankInfo(request)

    def update_bank_info(self, bank_info_id, mfo, account_number, receipant_name):
        request = startup_pb2.UpdateBankInfoRequest(
            bank_info_id=bank_info_id,
            mfo=mfo,
            account_number=account_number,
            receipant_name=receipant_name,
        )
        return self.stub.UpdateBankInfo(request)

    def delete_bank_info(self, bank_info_id):
        request = startup_pb2.DeleteBankInfoRequest(bank_info_id=bank_info_id)
        return self.stub.DeleteBankInfo(request)

    def create_compaign_update(self, compaign_id, title, body):
        request = startup_pb2.CreateCompaignUpdateRequest(
            compaign_id=compaign_id,
            title=title,
            body=body,
        )
        return self.stub.CreateCompaignUpdate(request)

    def update_compaign_update(self, update_id, title, body):
        request = startup_pb2.UpdateCompaignUpdateRequest(
            update_id=update_id,
            title=title,
            body=body,
        )
        return self.stub.UpdateCompaignUpdate(request)

    def delete_compaign_update(self, update_id):
        request = startup_pb2.DeleteCompaignUpdateRequest(update_id=update_id)
        return self.stub.DeleteCompaignUpdate(request)

    def get_startup(self, startup_id):
        request = startup_pb2.GetStartupRequest(startup_id=startup_id)
        return self.stub.GetStartup(request)

    def get_compaigns(self, campaign_id):
        request = startup_pb2.GetCompaignsRequest(campaign_id=campaign_id)
        return self.stub.GetCompaigns(request)

    def get_bank_info(self, bank_info_id):
        request = startup_pb2.GetBankInfoRequest(bank_info_id=bank_info_id)
        return self.stub.GetBankInfo(request)

    def get_compaign_update(self, update_id):
        request = startup_pb2.GetCompaignUpdateRequest(update_id=update_id)
        return self.stub.GetCompaignUpdate(request)

    def list_startups(self, page: int = 1, limit: int = 9, status: str = None):
        request = startup_pb2.ListStartupsRequest(
            page=page, limit=limit, status=status or ""
        )
        return self.stub.ListStartups(request)

    def get_startups_by_user(self, user_id: int):
        request = startup_pb2.GetStartupsByUserRequest(user_id=user_id)
        return self.stub.GetStartupsByUser(request)

    def list_categories(self):
        request = startup_pb2.ListCategoriesRequest()
        return self.stub.ListCategories(request)

    def list_campaigns_by_startup(self, startup_id: int):
        request = startup_pb2.ListCampaignsByStartupRequest(startup_id=startup_id)
        return self.stub.ListCampaignsByStartup(request)
