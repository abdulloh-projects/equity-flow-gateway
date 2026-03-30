import json

import grpc
from apps.generated import auth_pb2, auth_pb2_grpc
from decouple import config


class AuthService:
    def __init__(self):
        service_config = json.dumps({"loadBalancingConfig": [{"round_robin": {}}]})
        auth_url = config("AUTH_URL")
        self.channel = grpc.insecure_channel(
            auth_url, options=[("grpc.service_config", service_config)]
        )
        self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)

    def register(self, email, password, first_name, last_name, role):
        request = auth_pb2.RegisterRequest(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=auth_pb2.UserRole.Value(role),
        )
        response = self.stub.Register(request)
        return response

    def login(self, email, password):
        request = auth_pb2.LoginRequest(
            email=email,
            password=password,
        )
        response = self.stub.Login(request)
        return response

    def send_otp(self, email):
        request = auth_pb2.SendOtpRequest(
            email=email,
        )
        response = self.stub.SendOtp(request)
        return response

    def verify_otp(self, email, otp):
        request = auth_pb2.VerifyOtpRequest(
            email=email,
            otp=otp,
        )
        response = self.stub.VerifyOtp(request)
        return response

    def decode_token(self, token):
        request = auth_pb2.DecodeTokenRequest(
            token=token,
        )
        response = self.stub.DecodeToken(request)
        return response
