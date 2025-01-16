from datetime import datetime
import traceback
import sys
import logging
from typing import Any, Dict, List, Optional
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, field_validator
from email_validator import validate_email, EmailNotValidError

# Use INFO level by default
logger = logging.getLogger(__name__)


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
        async with self._lock:
            now = datetime.utcnow()

            if self._last_email_time:
                time_diff = (now - self._last_email_time).total_seconds()
                if time_diff > self.email_config.rate_limit_period:
                    self._email_count_in_period = 0

            if self._email_count_in_period >= self.email_config.rate_limit_count:
                logger.warning("Email rate limit exceeded, skipping email notification")
                return False

            self._email_count_in_period += 1
            self._last_email_time = now
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

            await smtp.connect()

            try:
                await smtp.login(
                    self.email_config.smtp_username, self.email_config.smtp_password
                )
                await smtp.send_message(message)
                logger.info("Crash report email sent successfully")

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
        error_report = self._format_error_report(error, request, context)
        subject = f"BSS Backend Error: {type(error).__name__}"

        await self._send_email(subject, error_report)
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)


def setup_crash_reporting(app: FastAPI, email_config: EmailConfig) -> CrashReporter:
    crash_reporter = CrashReporter(email_config)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> None:
        if not isinstance(exc, HTTPException):  # Only report non-HTTP exceptions
            await crash_reporter.report_error(exc, request)
        raise exc  # Re-raise the exception for FastAPI to handle

    return crash_reporter
