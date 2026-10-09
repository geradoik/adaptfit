"""AdaptFit API entry point: /api/health, plus metrics for a user and for the simulated demo persona."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from . import db, demo_seed, metrics_service


def get_db_path() -> str:
    return os.getenv("ADAPTFIT_DB", "adaptfit.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = db.connect(get_db_path())
    try:
        db.init_db(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="AdaptFit API", version="0.1.0", lifespan=lifespan)


@app.get("/api/health")
def health():
    # One connection per request: sync endpoints run in a thread pool and SQLite connections are not shared across threads.
    conn = db.connect(get_db_path())
    try:
        return {"status": "ok", **db.health(conn)}
    finally:
        conn.close()


def _metrics_for(conn, user_id: int, as_of: str | None):
    try:
        return metrics_service.metrics_report(conn, user_id, as_of)
    except LookupError:
        raise HTTPException(status_code=404, detail="User not found")
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of must be YYYY-MM-DD")


@app.get("/api/users/{user_id}/metrics")
def user_metrics(user_id: int, as_of: str | None = None):
    conn = db.connect(get_db_path())
    try:
        return _metrics_for(conn, user_id, as_of)
    finally:
        conn.close()


@app.get("/api/demo/metrics")
def demo_metrics():
    """Metrics for the simulated demo persona; creates it on first use (python -m app.demo_seed does the same)."""
    conn = db.connect(get_db_path())
    try:
        uid = demo_seed.seed_demo(conn)
        return _metrics_for(conn, uid, None)
    finally:
        conn.close()
