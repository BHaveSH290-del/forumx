from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router as auth_router
from app.api.communities import router as communities_router
from app.api.users import router as users_router
from app.core.db import SessionLocal


app = FastAPI(title="ForumX API")
app.include_router(auth_router)
app.include_router(communities_router)
app.include_router(users_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        return {"status": "error", "database": "disconnected"}
