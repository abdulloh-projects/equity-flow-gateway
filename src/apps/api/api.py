from fastapi import APIRouter

from .endpoints import auth, startup

router = APIRouter()


router.include_router(auth.router)
router.include_router(startup.router)
