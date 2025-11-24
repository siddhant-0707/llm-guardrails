"""FastAPI application entry point"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.observability import setup_observability
from app.routes import health, guardrails, agents, models

logger = logging.getLogger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="LLM Guardrails & Observability Service",
        description="Production-ready LLM guardrails with prompt injection detection, "
        "PII redaction, content policy checks, and comprehensive observability",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # Setup OpenTelemetry observability
    setup_observability(app)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(guardrails.router, prefix="/api/v1/guardrails", tags=["guardrails"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["models"])

    @app.on_event("startup")
    async def startup_event():
        """Startup event handler"""
        logger.info(f"Starting LLM Guardrails Service in {settings.environment} mode")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler"""
        logger.info("Shutting down LLM Guardrails Service")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )

