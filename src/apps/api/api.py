from fastapi import APIRouter

from .endpoints import auth, chatbot, startup, invest, messages, analysis, media

router = APIRouter()

router.include_router(auth.router)
router.include_router(startup.router)
router.include_router(media.router)
router.include_router(chatbot.router)
router.include_router(invest.router)
router.include_router(messages.router)
router.include_router(analysis.router)
