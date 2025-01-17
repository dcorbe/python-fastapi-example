import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import AuthConfig, AuthService, create_auth_router, setup_auth
from auth.config import (
    JWTConfig,
    get_jwt_config,
    initialize_jwt_config,
    initialize_redis_config,
)
from config import Settings, get_settings
from config.logging import jwt_log, redis_log
from example import router as example_router
from monitoring import CrashReporter, EmailConfig, setup_crash_reporting
from monitoring.crash_reporter import debug_log
from v1.users.router import router as users_router

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT,
)

# Module logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


class Application(FastAPI):
    """FastAPI application with additional functionality."""

    settings: Union[Settings, None] = None
    jwt_config: Union[JWTConfig, None] = None
    email_config: Union[EmailConfig, None] = None
    crash_reporter: Union[CrashReporter, None] = None
    auth_config: Union[AuthConfig, None] = None
    auth_service: Union[AuthService, None] = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Initialize FastAPI with settings from config
        super().__init__(
            *args,
            title=settings.API_TITLE,
            description=settings.API_DESCRIPTION,
            version=settings.API_VERSION,
            **kwargs,
        )
        self._initialized = False

        # Configure CORS middleware using settings
        self.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        )

        @self.on_event("shutdown")
        async def shutdown_event() -> None:
            """Close Redis connection on shutdown."""
            from auth.dependencies import get_redis_service

            try:
                redis_service = get_redis_service()
                await redis_service.close()
                redis_log("Redis connection closed on shutdown")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")

    async def initialize(self) -> None:
        """Initialize application components."""
        if self._initialized:
            return
        self._initialized = True

        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format=settings.LOG_FORMAT,
            datefmt=settings.LOG_DATE_FORMAT,
        )
        self.settings = get_settings()

        # Initialize JWT and Redis configs
        initialize_jwt_config()
        initialize_redis_config()
        self.jwt_config = get_jwt_config()

        self.email_config = EmailConfig(
            smtp_host=self.settings.EMAIL_HOST,
            smtp_port=self.settings.EMAIL_PORT,
            smtp_username=self.settings.EMAIL_USERNAME,
            smtp_password=self.settings.EMAIL_PASSWORD,
            from_email=self.settings.EMAIL_FROM,
            to_emails=[
                email.strip()
                for email in self.settings.EMAIL_TO.split(",")
                if email.strip()
            ],
            rate_limit_period=self.settings.ERROR_RATE_LIMIT_PERIOD,
            rate_limit_count=self.settings.ERROR_RATE_LIMIT_COUNT,
        )

        # Initialize crash reporting before anything else
        debug_log("Initializing crash reporter before other middleware...")
        self.crash_reporter = setup_crash_reporting(self, self.email_config)

        # Now configure other middleware
        debug_log("Configuring additional middleware...")
        debug_log("All middleware configured")
        jwt_log("Setting up authentication...")
        self.auth_config = AuthConfig.from_env()

        # Initialize auth service
        self.auth_service = await setup_auth(self, self.auth_config)

        # Include routers
        auth_router = create_auth_router(self.auth_service)
        self.include_router(auth_router.router)
        self.include_router(users_router, prefix="/v1")
        self.include_router(example_router)


@asynccontextmanager
async def lifespan(app: Application) -> AsyncGenerator[None, None]:
    """Handle application lifecycle events."""
    await app.initialize()
    yield
    # Cleanup handled in shutdown_event


# Create application instance with lifespan context manager
app = Application(lifespan=lifespan)
