from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, companies, dashboard, health, redis, environment_variables

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(redis.router, prefix="/redis", tags=["Redis"])
api_router.include_router(environment_variables.router, prefix="/environment-variables", tags=["Environment Variables"])
