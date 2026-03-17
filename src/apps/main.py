from apps.api.api import router as api_router
from decouple import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Equity Flow API Gateway",
    description="API Gateway for Equity Flow Microservices",
    version="1.0.0",
    # openapi_url=f"/api/openapi.json",
    # docs_url=f"/api/docs",
    # redoc_url=f"/api/redoc",/
)
origins = config(
    "ORIGINS",
    default=[],
    cast=lambda v: [s.strip() for s in v.split(",")] if isinstance(v, str) else v,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
