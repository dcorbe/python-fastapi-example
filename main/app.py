from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from monitoring import CrashReporter, setup_crash_reporting, EmailConfig
from auth import setup_auth, AuthService, AuthConfig
from auth.config import initialize_jwt_config, get_jwt_config, JWTConfig
from config import Settings, get_settings


class Application(FastAPI):
    settings: Settings | None = None
    jwt_config: JWTConfig | None = None
    email_config: EmailConfig | None = None
    crash_reporter: CrashReporter | None = None
    auth_config: AuthConfig | None = None
    auth_service: AuthService | None = None

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

    def init(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self.settings = get_settings()
        self._cors_configuration()
        initialize_jwt_config()
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
        self.crash_reporter = setup_crash_reporting(self, self.email_config)

        self.auth_config = AuthConfig(
            jwt_secret_key=self.settings.JWT_SECRET,
            jwt_algorithm=self.settings.JWT_ALGORITHM,
            access_token_expire_minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            max_login_attempts=self.settings.MAX_LOGIN_ATTEMPTS,
            lockout_minutes=self.settings.LOCKOUT_MINUTES,
        )
        self.auth_service = setup_auth(self, self.auth_config)

    # TODO: Do not allow all origins in production
    def _cors_configuration(self) -> None:
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
