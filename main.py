"""Main FastAPI application."""
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from example import router as example_router
from api.v1 import router as api_v1_router
from database import Database
from monitoring import setup_crash_reporting, EmailConfig
from auth import setup_auth, AuthConfig
from auth.config import initialize_jwt_config, get_jwt_config
from config import get_settings

app = FastAPI()

# CORS configuration.   TODO: Do not allow all origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()

initialize_jwt_config()
jwt_config = get_jwt_config()

email_config = EmailConfig(
    smtp_host=settings.SMTP_HOST,
    smtp_port=settings.SMTP_PORT,
    smtp_username=settings.SMTP_USERNAME,
    smtp_password=settings.SMTP_PASSWORD,
    from_email=settings.get_from_email(),
    to_emails=settings.get_email_list(),
    rate_limit_period=settings.ERROR_RATE_LIMIT_PERIOD,
    rate_limit_count=settings.ERROR_RATE_LIMIT_COUNT,
)
crash_reporter = setup_crash_reporting(app, email_config)

auth_config = AuthConfig(
    jwt_secret_key=settings.JWT_SECRET,
    jwt_algorithm=settings.JWT_ALGORITHM,
    access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    max_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
    lockout_minutes=settings.LOCKOUT_MINUTES
)
auth_service = setup_auth(app, auth_config)

# TODO: Investigate on_event deprecation warnings emitted here
@app.on_event("startup")
async def startup() -> None:
    """Initialize database on startup."""
    Database.init()

@app.on_event("shutdown")
async def shutdown() -> None:
    """Close database on shutdown."""
    await Database.close()

app.include_router(example_router)
app.include_router(api_v1_router)

@app.get("/")
async def hello() -> Dict[str, str]:
    """Hello world endpoint."""
    return {"Hello": "World"}

@app.get("/crash-test-dummy")
async def test_crash() -> None:
    """This will raise a ZeroDivisionError"""
    1 / 0

# Do not allow this app to be called directly from the command line
if __name__ == "__main__":
    raise RuntimeError("Use 'fastapi dev main.py' to run this application")
