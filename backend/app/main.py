from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.core.redis import close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    yield
    # Shutdown
    await close_redis_client()


app = FastAPI(
    title="AI-BOS Backend",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    openapi_tags=[
        {"name": "Auth", "description": "Authentication operations"},
        {"name": "Users", "description": "User management operations"},
        {"name": "Companies", "description": "Company management operations"},
        {"name": "Dashboard", "description": "Dashboard operations"},
        {"name": "Redis", "description": "Redis cache management operations"},
        {"name": "Tenants", "description": "Multi-tenancy management operations"},
        {"name": "Audit Logs", "description": "Audit log and activity tracking operations"},
        {"name": "Tokens", "description": "Token management and revocation operations"},
    ],
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
