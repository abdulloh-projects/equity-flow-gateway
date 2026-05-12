import json
import logging
import re

import ollama
import redis.asyncio as aioredis
from apps.api.deps import get_current_user
from apps.services.startup_service import StartupService
from decouple import config
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/startup", tags=["analysis"])

_OLLAMA_URL: str = config("OLLAMA_URL", default="http://localhost:11434")
_LLM_MODEL: str = config("LLM_MODEL", default="qwen2.5:3b")
_REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379/0")
_ANALYSIS_TTL: int = 86400  # 24 hours

_redis: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(_REDIS_URL, decode_responses=True)
    return _redis


_ANALYSIS_SYSTEM_PROMPT = """You are an expert startup investment analyst. Analyze the following startup data and provide a comprehensive investment assessment.

Return your analysis as valid JSON with exactly these fields:
- "summary": a 2-3 sentence plain-text summary of the startup
- "confidence_score": integer 0-100 (how confident you are in your assessment)
- "chance_of_winning": integer 0-100 (probability of this startup becoming successful)
- "risk_level": one of "Low", "Medium", "High", "Very High"
- "growth_prediction": a plain-text 12-month growth prediction
- "strengths": array of 2-4 plain-text strings
- "risks": array of 2-4 plain-text strings
- "recommendation": one of "Strong Buy", "Moderate Buy", "Hold", "Avoid"

Be objective and data-driven. Base your analysis on the provided financial metrics, market signals, and team information.
"""


class AnalysisRequest(BaseModel):
    startup_id: int = Field(...)
    startup_name: str = ""
    description: str = ""
    location: str = ""
    founded_at: str = ""
    team_size: int = 0
    website_url: str = ""
    campaign_data: str = ""


class AnalysisResponse(BaseModel):
    success: bool
    analysis: dict = {}


@router.post("/{startup_id}/analyze", response_model=AnalysisResponse)
async def analyze_startup(
    startup_id: int,
    user_id: str = Depends(get_current_user),
):
    try:
        cache_key = f"analysis:startup:{startup_id}"
        redis = await _get_redis()
        cached = await redis.get(cache_key)
        if cached:
            logger.info("Cache hit for startup %d analysis", startup_id)
            return AnalysisResponse(success=True, analysis=json.loads(cached))

        svc = StartupService()
        startup_res = svc.get_startup(startup_id)
        campaigns_res = svc.list_campaigns_by_startup(startup_id)

        startup_data = {}
        if hasattr(startup_res, "data") and startup_res.data:
            d = startup_res.data
            startup_data = {
                "startup_name": getattr(d, "name", ""),
                "description": getattr(d, "description", ""),
                "location": getattr(d, "location", ""),
                "founded_at": str(getattr(d, "founded_at", "")),
                "team_size": getattr(d, "team_size", 0),
                "website_url": getattr(d, "website_url", ""),
            }

        campaigns_list = []
        if hasattr(campaigns_res, "campaigns") and campaigns_res.campaigns:
            campaigns_list = [
                {
                    "target_amount": getattr(c, "target_amount", 0),
                    "raised_amount": getattr(c, "raised_amount", 0),
                    "min_investment": getattr(c, "min_investment", 0),
                    "valuation": getattr(c, "valuation", 0),
                    "revenue": getattr(c, "revenue", 0),
                    "revenue_share": getattr(c, "revenue_share", 0),
                    "burn_rate": getattr(c, "burn_rate", 0),
                    "runway": getattr(c, "runway", 0),
                    "gross_margin": getattr(c, "gross_margin", 0),
                    "status": getattr(c, "status", ""),
                    "deadline": str(getattr(c, "deadline", "")),
                }
                for c in campaigns_res.campaigns
            ]

        prompt_data = json.dumps(
            {
                "startup": startup_data,
                "campaigns": campaigns_list,
            },
            indent=2,
        )

        logger.info("Analyzing startup %d with Ollama", startup_id)
        client = ollama.Client(host=_OLLAMA_URL)
        raw = client.chat(
            model=_LLM_MODEL,
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this startup:\n\n{prompt_data}"},
            ],
        )
        reply: str = raw.message.content

        text = re.sub(r"```(?:json|JSON)?\s*", "", reply).replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}")
        json_str = text[start : end + 1] if start != -1 and end > start else text

        try:
            analysis = json.loads(json_str)
        except json.JSONDecodeError:
            analysis = {
                "summary": "Analysis could not be parsed. Please try again.",
                "confidence_score": 50,
                "chance_of_winning": 50,
                "risk_level": "Medium",
                "growth_prediction": "Unable to generate structured analysis.",
                "strengths": [],
                "risks": [],
                "recommendation": "Hold",
            }

        await redis.setex(cache_key, _ANALYSIS_TTL, json.dumps(analysis))
        return AnalysisResponse(success=True, analysis=analysis)

    except Exception as exc:
        logger.exception("Analysis error for startup %d: %s", startup_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))
