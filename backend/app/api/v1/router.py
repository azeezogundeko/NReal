"""
API router for version 1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import profiles, rooms, voices, tokens

# Create the main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(voices.router, prefix="/voices", tags=["voices"])
api_router.include_router(tokens.router, prefix="/token", tags=["tokens"])
