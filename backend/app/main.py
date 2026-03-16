"""
AgentOS-Goldmine · FastAPI Application
Real-time autonomous trading research platform
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import router
from app.api.websocket import ws_router
from app.db.session import init_db
from app.core.config import settings

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger()

REQUEST_COUNT = Counter(
    "goldmine_http_requests_total", "Total HTTP requests", ["method", "endpoint"]
)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("🚀 AgentOS-Goldmine starting", version="1.0.0")
    await init_db()
    import os
    os.makedirs("workspace", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    yield
    logger.info("🛑 AgentOS-Goldmine shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgentOS-Goldmine API",
        description="💎 Autonomous AI Trading Research Platform — Raw market data → Gold signals",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/ws")

    # Serve generated reports
    import os
    os.makedirs("reports", exist_ok=True)
    app.mount("/reports", StaticFiles(directory="reports"), name="reports")

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "healthy", "service": "AgentOS-Goldmine", "version": "1.0.0"}

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
        response = await call_next(request)
        return response

    return app


app = create_app()
