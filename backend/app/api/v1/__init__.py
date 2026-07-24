from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, companies, dashboard, health, redis, environment_variables, tenant, audit_log, tokens

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(redis.router, prefix="/redis", tags=["Redis"])
api_router.include_router(environment_variables.router, prefix="/environment-variables", tags=["Environment Variables"])
api_router.include_router(tenant.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(audit_log.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["Tokens"])
