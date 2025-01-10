from database import Database

db: Database | None = None

async def get_db() -> Database:
    if db is None:
        raise RuntimeError("Database not initialized")
    return db
