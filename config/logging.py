import logging
from functools import lru_cache

from config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_startup_logger() -> logging.Logger:
    """Get a logger for startup/initialization messages."""
    return logging.getLogger("startup")


def redis_log(msg: str) -> None:
    """Log Redis-related messages only if REDIS_DEBUG is enabled."""
    if get_settings().REDIS_DEBUG:
        get_startup_logger().info(msg)


def jwt_log(msg: str) -> None:
    """Log JWT-related messages only if AUTH_DEBUG is enabled."""
    if get_settings().AUTH_DEBUG:
        get_startup_logger().info(msg)
