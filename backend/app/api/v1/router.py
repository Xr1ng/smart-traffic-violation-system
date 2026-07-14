# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1 import (
    analysis,
    announcements,
    audit_logs,
    auth,
    cameras,
    cases,
    intakes,
    media,
    rewards,
    roles,
    rules,
    statistics,
    users,
    vehicles,
    violations,
)
from app.api.v1.auth import permissions_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(permissions_router)
api_router.include_router(intakes.router)
api_router.include_router(cases.router)
api_router.include_router(media.router)
api_router.include_router(violations.router)
api_router.include_router(statistics.router)
api_router.include_router(cameras.router)
api_router.include_router(users.router)
api_router.include_router(vehicles.router)
api_router.include_router(vehicles.citizen_router)
api_router.include_router(rewards.router)
api_router.include_router(rules.router)
api_router.include_router(analysis.router)
api_router.include_router(roles.router)
api_router.include_router(audit_logs.router)
api_router.include_router(announcements.router)
api_router.include_router(announcements.admin_router)
