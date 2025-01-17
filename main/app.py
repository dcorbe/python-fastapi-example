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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Application(FastAPI):
    """FastAPI application with additional functionality."""

    settings: Union[Settings, None] = None
    jwt_config: Union[JWTConfig, None] = None
    email_config: Union[EmailConfig, None] = None
    crash_reporter: Union[CrashReporter, None] = None
    auth_config: Union[AuthConfig, None] = None
    auth_service: Union[AuthService, None] = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Initialize FastAPI with just the essential OpenAPI settings
        super().__init__(
            *args,
            title="BSS Backend API",
            description="Bridge Security Solutions Backend API",
            version="0.1.0",
            **kwargs,
        )
        self._initialized = False

        # Configure CORS middleware during initialization
        # TODO: Do not allow all origins in production
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
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

        logging.basicConfig(level=logging.INFO)
        self.settings = get_settings()

        # Initialize JWT and Redis configs
        initialize_jwt_config()
        initialize_redis_config()
        self.jwt_config = get_jwt_config()

        self.email_config = EmailConfig(
            smtp_host=self.settings.SMTP_HOST,
            smtp_port=self.settings.SMTP_PORT,
            smtp_username=self.settings.SMTP_USERNAME,
            smtp_password=self.settings.SMTP_PASSWORD,
            from_email=self.settings.get_from_email(),
            to_emails=self.settings.get_email_list(),
            rate_limit_period=self.settings.ERROR_RATE_LIMIT_PERIOD,
            rate_limit_count=self.settings.ERROR_RATE_LIMIT_COUNT,
        )

        # Initialize crash reporting before anything else
        debug_log("Initializing crash reporter before other middleware...")
        self.crash_reporter = setup_crash_reporting(self, self.email_config)

        # Now configure other middleware
        debug_log("Configuring additional middleware...")
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        debug_log("All middleware configured")
        jwt_log("Setting up authentication...")
        self.auth_config = AuthConfig(
            jwt_secret_key=self.settings.JWT_SECRET,
            jwt_algorithm=self.settings.JWT_ALGORITHM,
            access_token_expire_minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            max_login_attempts=self.settings.MAX_LOGIN_ATTEMPTS,
            lockout_minutes=self.settings.LOCKOUT_MINUTES,
        )

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
