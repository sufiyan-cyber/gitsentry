"""FastAPI Application Entrypoint for GitSentry Webhook Receiver."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common.config import get_settings
from common.publisher import get_event_publisher
from common.secrets import get_secret_manager
from services.receiver.routes import router as webhook_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("gitsentry.receiver")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    settings = get_settings()
    logger.info("Starting GitSentry Webhook Receiver on environment '%s'", settings.ENVIRONMENT)
    logger.info("GCP Project ID: %s | Pub/Sub Topic: %s", settings.GCP_PROJECT_ID, settings.PUBSUB_TOPIC_PR_EVENTS)

    # Pre-warm Secret Manager & Publisher
    try:
        secret_mgr = get_secret_manager(settings)
        publisher = get_event_publisher(settings)
        logger.info("Initialized Secret Manager and Pub/Sub publisher successfully")
    except Exception as e:
        logger.warning("Startup pre-warming encountered warning: %s", e)

    yield

    logger.info("Shutting down GitSentry Webhook Receiver...")


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="GitSentry Webhook Receiver",
        description="High-throughput, HMAC-verified GitHub webhook receiver decoupled via Google Cloud Pub/Sub",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(webhook_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error occurred while processing webhook",
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "services.receiver.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
