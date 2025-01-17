import logging
from typing import Dict

from .app import app

logger = logging.getLogger(__name__)


@app.get("/")
async def hello() -> Dict[str, str]:
    """Hello world endpoint."""
    return {"Hello": "World"}


@app.get("/crash-test-dummy")
async def test_crash() -> None:
    """This will raise a ZeroDivisionError"""
    logger.info(
        f"Exception handlers before crash: {list(app.exception_handlers.keys())}"
    )
    1 / 0


__all__ = ["app"]

if __name__ == "__main__":
    raise RuntimeError("Please use 'fastapi dev main' to run this application")
