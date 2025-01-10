from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from example import router as example_router
from database import Database
import database_manager

app = FastAPI()

# TODO: Do not set allow_origins to "*" in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Investigate the deprecation warnings for on_event
@app.on_event("startup")
async def startup() -> None:
    database_manager.db = await Database.connect()

@app.on_event("shutdown")
async def shutdown() -> None:
    if database_manager.db:
        await database_manager.db.close()
        database_manager.db = None

app.include_router(auth_router)
app.include_router(example_router)

@app.get("/")
async def hello() -> Dict[str, str]:
    return {"Hello": "World"}
