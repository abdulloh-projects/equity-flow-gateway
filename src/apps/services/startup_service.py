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
        self.stub = startup_pb2_grpc.StartupStub(self.channel)

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

    def create_compaign(
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
        request = startup_pb2.CreateCompaignRequest(
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
        return self.stub.CreateCompaign(request)

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

    def create_compaign_update(self, compaign_id, title, body):
        request = startup_pb2.CreateCompaignUpdateRequest(
            compaign_id=compaign_id,
            title=title,
            body=body,
        )
        return self.stub.CreateCompaignUpdate(request)
