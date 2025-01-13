from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from example import router as example_router
from api.v1 import router as api_v1_router
from database import Database
import database_manager
from monitoring import setup_crash_reporting, EmailConfig
from auth import setup_auth, AuthConfig
import os

app = FastAPI()

# TODO: Do not set allow_origins to "*" in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup crash reporting
email_config = EmailConfig(
    smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
    smtp_port=int(os.getenv("SMTP_PORT", "465")),
    smtp_username=os.getenv("SMTP_USERNAME", ""),
    smtp_password=os.getenv("SMTP_PASSWORD", ""),
    from_email=os.getenv("FROM_EMAIL", "") or os.getenv("SMTP_USERNAME", ""),  # Use SMTP_USERNAME as fallback
    to_emails=[email.strip() for email in os.getenv("TO_EMAILS", "").split(",") if email.strip()],
    rate_limit_period=int(os.getenv("ERROR_RATE_LIMIT_PERIOD", "300")),
    rate_limit_count=int(os.getenv("ERROR_RATE_LIMIT_COUNT", "10")),
)
crash_reporter = setup_crash_reporting(app, email_config)

# JWT secret is guaranteed to exist due to the check above
jwt_secret = os.getenv("JWT_SECRET")
assert jwt_secret is not None  # This tells mypy that jwt_secret is not None

# Setup authentication
auth_config = AuthConfig(
    jwt_secret_key=jwt_secret,  # Now mypy knows this is str, not Optional[str]
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
    lockout_minutes=int(os.getenv("LOCKOUT_MINUTES", "15"))
)
auth_service = setup_auth(app, auth_config)

@app.on_event("startup")
async def startup() -> None:
    database_manager.db = await Database.connect()

@app.on_event("shutdown")
async def shutdown() -> None:
    if database_manager.db:
        await database_manager.db.close()
        database_manager.db = None

app.include_router(example_router)
app.include_router(api_v1_router)

@app.get("/")
async def hello() -> Dict[str, str]:
    return {"Hello": "World"}

@app.get("/crash-test-dummy")
async def test_crash() -> None:
    # This will raise a ZeroDivisionError
    1 / 0  # Changed to expression statement instead of return
