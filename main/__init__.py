from database import Database
from typing import Dict

from .app import Application

from example import router as example_router
from api.v1 import router as api_v1_router

# Create an instance of the custom Application class
app = Application()

# TODO: Investigate on_event deprecation warnings emitted here
@app.on_event("startup")
async def startup() -> None:
    """Initialize database on startup."""
    Database.init()

@app.on_event("shutdown")
async def shutdown() -> None:
    """Close database on shutdown."""
    await Database.close()

app.init()
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

__all__ = ["app"]

if __name__ == "__main__":
    raise RuntimeError("Please use 'fastapi dev main' to run this application")
