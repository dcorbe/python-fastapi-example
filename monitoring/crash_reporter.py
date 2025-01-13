from datetime import datetime
import json
import logging
import sys
import traceback
from typing import Any, Dict, Optional, List
import asyncio
from enum import Enum
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from pydantic import BaseModel, EmailStr
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ErrorCategory(str, Enum):
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    NETWORK = "network"
    INTERNAL = "internal"
    EXTERNAL_SERVICE = "external_service"

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
    use_tls: bool = True
    rate_limit_period: int = 300  # 5 minutes in seconds
    rate_limit_count: int = 10    # max emails per period
    
    def model_pre_init(self, data: Any) -> None:
        # Validate email addresses
        if 'from_email' in data:
            data['from_email'] = validate_email_str(data['from_email'])
        if 'to_emails' in data:
            data['to_emails'] = [validate_email_str(email) for email in data['to_emails']]

class CrashReporter:
    def __init__(self, email_config: EmailConfig) -> None:
        self.email_config = email_config
        self._error_counts: Dict[str, int] = {}
        self._last_email_time: Optional[datetime] = None
        self._email_count_in_period: int = 0
        self._lock = asyncio.Lock()
        
    def _categorize_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        if isinstance(error, RequestValidationError):
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        
        error_str = str(error).lower()
        if "database" in error_str or "sql" in error_str or "psycopg" in error_str:
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH
        elif "unauthorized" in error_str or "forbidden" in error_str or "token" in error_str:
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH
        elif "timeout" in error_str or "connection" in error_str:
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        elif "service" in error_str or "api" in error_str:
            return ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.MEDIUM
        
        return ErrorCategory.INTERNAL, ErrorSeverity.HIGH

    async def _can_send_email(self) -> bool:
        async with self._lock:
            now = datetime.utcnow()
            
            if self._last_email_time:
                time_diff = (now - self._last_email_time).total_seconds()
                if time_diff > self.email_config.rate_limit_period:
                    self._email_count_in_period = 0
            
            if self._email_count_in_period >= self.email_config.rate_limit_count:
                return False
            
            self._email_count_in_period += 1
            self._last_email_time = now
            return True

    async def _send_email(self, subject: str, body: str) -> None:
        if not await self._can_send_email():
            logger.warning("Email rate limit exceeded, skipping email notification")
            return

        message = MIMEText(body, "plain")
        message["From"] = self.email_config.from_email
        message["To"] = ", ".join(self.email_config.to_emails)
        message["Subject"] = subject
        
        try:
            async with aiosmtplib.SMTP(
                hostname=self.email_config.smtp_host,
                port=self.email_config.smtp_port,
                use_tls=self.email_config.use_tls,
            ) as smtp:
                await smtp.login(
                    self.email_config.smtp_username,
                    self.email_config.smtp_password
                )
                await smtp.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send error notification email: {str(e)}")

    def _format_error_email(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        request: Optional[Request],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        timestamp = datetime.utcnow().isoformat()
        error_type = type(error).__name__
        error_location = f"{error.__class__.__module__}.{error.__class__.__name__}"
        
        exc_info = sys.exc_info()
        stack_trace = "".join(traceback.format_exception(*exc_info))
        
        error_key = f"{error_location}: {str(error)}"
        error_count = self._error_counts.get(error_key, 0)
        
        # Build the message in plain text
        lines = [
            "Bridge Security Solutions Backend Error Report",
            "=" * 50,
            f"Timestamp: {timestamp}",
            f"Error Type: {error_type}",
            f"Category: {category.value}",
            f"Severity: {severity.value}",
            f"Error Location: {error_location}",
            f"Error Message: {str(error)}",
            f"Occurrence Count: {error_count + 1}",
            ""
        ]

        if request:
            lines.extend([
                "Request Information:",
                "-" * 20,
                f"Method: {request.method}",
                f"URL: {request.url}",
                f"Headers: {dict(request.headers)}",
                f"Client Host: {request.client.host if request.client else 'Unknown'}",
                ""
            ])

        if additional_context:
            lines.extend([
                "Additional Context:",
                "-" * 20,
                json.dumps(additional_context, indent=2),
                ""
            ])

        lines.extend([
            "Stack Trace:",
            "-" * 20,
            stack_trace
        ])

        return "\n".join(lines)

    async def report_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        error_key = f"{error.__class__.__module__}.{error.__class__.__name__}: {str(error)}"
        category, severity = self._categorize_error(error)
        
        async with self._lock:
            self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        email_body = self._format_error_email(
            error, category, severity, request, additional_context
        )
        subject = f"BSS Backend Error: [{severity.value.upper()}] {category.value}: {type(error).__name__}"
        
        await self._send_email(subject, email_body)
        logger.error(
            f"Error reported: {error_key} "
            f"[Category: {category.value}, Severity: {severity.value}]",
            exc_info=True
        )

def setup_crash_reporting(app: FastAPI, email_config: EmailConfig) -> CrashReporter:
    crash_reporter = CrashReporter(email_config)
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> None:
        if not isinstance(exc, HTTPException):  # Don't report 404s, etc.
            await crash_reporter.report_error(exc, request)
        raise exc  # Re-raise the exception for FastAPI to handle
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> None:
        await crash_reporter.report_error(
            exc,
            request,
            {"validation_errors": exc.errors()}
        )
        raise exc
    
    return crash_reporter
