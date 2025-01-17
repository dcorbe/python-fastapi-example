import asyncio
import logging
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import aiosmtplib
from email_validator import EmailNotValidError, validate_email
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, field_validator
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from config.settings import get_settings

# Module initialization
__all__ = ["CrashReporter", "EmailConfig", "setup_crash_reporting"]

# Set up logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def debug_log(msg: str) -> None:
    """Log debug messages only if DEBUG_CRASH_REPORTER is enabled"""
    if get_settings().DEBUG_CRASH_REPORTER:
        logger.info(msg)


@dataclass
class MiddlewareConfig:
    """Configuration for crash reporter middleware to avoid circular imports"""

    logger: logging.Logger = logger


class CrashReporterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, crash_reporter: "CrashReporter") -> None:
        super().__init__(app)
        self.crash_reporter = crash_reporter
        self.config = MiddlewareConfig()
        debug_log("CrashReporterMiddleware initialized")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            if not isinstance(exc, HTTPException):
                debug_log(f"Middleware caught exception: {type(exc).__name__}")
                try:
                    await self.crash_reporter.report_error(exc, request)
                    debug_log("Error report sent successfully")
                except Exception as e:
                    logger.error(f"Failed to send error report: {e}")
            raise


def validate_email_str(email: str) -> str:
    try:
        email_info = validate_email(email, check_deliverability=False)
        return email_info.normalized
    except EmailNotValidError:
        raise ValueError(f"Invalid email address: {email}")


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    from_email: str
    to_emails: List[str]
    rate_limit_period: int = 300
    rate_limit_count: int = 10

    @field_validator("smtp_username")
    def validate_username(cls, v: str) -> str:
        if not v:
            raise ValueError("SMTP_USERNAME cannot be empty")
        return v

    @field_validator("smtp_password")
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("SMTP_PASSWORD cannot be empty")
        return v

    @field_validator("from_email")
    def validate_from_email(cls, v: str) -> str:
        if not v:
            raise ValueError("FROM_EMAIL cannot be empty")
        return validate_email_str(v)

    @field_validator("to_emails")
    def validate_to_emails(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("TO_EMAILS must contain at least one recipient")
        return [validate_email_str(email) for email in v]

    @field_validator("smtp_port")
    def validate_port(cls, v: int) -> int:
        if v not in [465, 587]:
            raise ValueError("SMTP_PORT must be either 465 (SSL) or 587 (STARTTLS)")
        return v


class CrashReporter:
    def __init__(self, email_config: EmailConfig) -> None:
        self.email_config = email_config
        self._last_email_time: Optional[datetime] = None
        self._email_count_in_period: int = 0
        self._lock = asyncio.Lock()

    async def _can_send_email(self) -> bool:
        debug_log("Checking if email can be sent...")
        async with self._lock:
            now = datetime.utcnow()

            if self._last_email_time:
                time_diff = (now - self._last_email_time).total_seconds()
                debug_log(f"Time since last email: {time_diff} seconds")
                if time_diff > self.email_config.rate_limit_period:
                    debug_log("Rate limit period expired, resetting count")
                    self._email_count_in_period = 0

            debug_log(f"Current email count in period: {self._email_count_in_period}")
            if self._email_count_in_period >= self.email_config.rate_limit_count:
                logger.warning("Email rate limit exceeded, skipping email notification")
                return False

            self._email_count_in_period += 1
            self._last_email_time = now
            debug_log("Email sending allowed")
            return True

    async def _send_email(self, subject: str, body: str) -> None:
        if not await self._can_send_email():
            return

        message = MIMEText(body, "plain")
        message["From"] = self.email_config.from_email
        message["To"] = ", ".join(self.email_config.to_emails)
        message["Subject"] = subject

        try:
            smtp = aiosmtplib.SMTP(
                hostname=self.email_config.smtp_host,
                port=self.email_config.smtp_port,
                use_tls=True,
            )

            debug_log(
                f"Attempting to connect to SMTP server {self.email_config.smtp_host}:{self.email_config.smtp_port}"
            )
            await smtp.connect()
            debug_log("Successfully connected to SMTP server")

            try:
                debug_log(
                    f"Attempting to login with username: {self.email_config.smtp_username}"
                )
                await smtp.login(
                    self.email_config.smtp_username, self.email_config.smtp_password
                )
                debug_log("Login successful, attempting to send message")
                await smtp.send_message(message)
                debug_log(
                    f"Message sent successfully to {', '.join(self.email_config.to_emails)}"
                )
                debug_log("Crash report email sent successfully")

            except aiosmtplib.SMTPAuthenticationError as auth_err:
                logger.error(f"Authentication failed: {str(auth_err)}")
                raise

            await smtp.quit()

        except Exception as e:
            logger.error(f"Failed to send error notification email: {str(e)}")
            raise

    def _format_error_report(
        self,
        error: Exception,
        request: Optional[Request] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        timestamp = datetime.utcnow().isoformat()
        exc_info = sys.exc_info()
        stack_trace = "".join(traceback.format_exception(*exc_info))

        lines = [
            "Bridge Security Solutions Backend Error Report",
            "=" * 50,
            f"Timestamp: {timestamp}",
            f"Error: {str(error)}",
            f"Type: {error.__class__.__name__}",
            "",
        ]

        if request:
            lines.extend(
                [
                    "Request Information:",
                    "-" * 20,
                    f"Method: {request.method}",
                    f"URL: {request.url}",
                    f"Client: {request.client.host if request.client else 'Unknown'}",
                    "",
                ]
            )

        if context:
            lines.extend(["Additional Context:", "-" * 20, str(context), ""])

        lines.extend(["Stack Trace:", "-" * 20, stack_trace])

        return "\n".join(lines)

    async def report_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        debug_log(f"Reporting error of type: {type(error).__name__}")
        error_report = self._format_error_report(error, request, context)
        subject = f"BSS Backend Error: {type(error).__name__}"

        debug_log("Attempting to send error report email...")
        try:
            await self._send_email(subject, error_report)
            debug_log("Error report email process completed")
        except Exception as e:
            logger.error(f"Failed to send error report: {str(e)}")
            raise
        finally:
            logger.error(f"Unhandled exception: {str(error)}", exc_info=True)


def setup_crash_reporting(app: FastAPI, email_config: EmailConfig) -> CrashReporter:
    debug_log("Setting up crash reporting...")
    crash_reporter = CrashReporter(email_config)
    debug_log("Created crash reporter instance")

    # Add our middleware at the beginning to catch exceptions before other middleware
    app.middleware_stack = None  # Reset middleware stack
    app.add_middleware(CrashReporterMiddleware, crash_reporter=crash_reporter)
    debug_log("Added crash reporter middleware")

    @app.on_event("startup")
    async def startup_event() -> None:
        debug_log("Crash reporter startup: Verifying middleware setup")
        # Just a startup verification log
        debug_log("Crash reporter startup complete")

    return crash_reporter
