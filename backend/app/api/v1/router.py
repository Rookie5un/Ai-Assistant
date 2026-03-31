from fastapi import APIRouter

from app.api.v1 import assistants, auth, conversations, dashboard, knowledge


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(assistants.router)
api_router.include_router(knowledge.router)
api_router.include_router(conversations.router)

