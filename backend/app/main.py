"""AdaptFit API entry point: /api/health, plus metrics for a user and for the simulated demo persona."""
import os
from contextlib import asynccontextmanager

from datetime import date

from fastapi import Body, FastAPI, HTTPException

from . import (ask_service, checkin_service, db, demo_seed, llm_client, metrics_service,
               onboarding_service, suggestion_service)


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
    # One connection per request
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


# --- onboarding, profile, check-in, suggestion -------------------------------------------------------------
# Each endpoint opens its own connection and maps service errors to a http code:
# LookupError -> 404, DuplicateCheckin -> 409, ValueError -> 422. Helps me know whats going on.

@app.get("/api/exercises")
def exercises():
    conn = db.connect(get_db_path())
    try:
        return checkin_service.list_exercises(conn)
    finally:
        conn.close()


@app.post("/api/onboarding", status_code=201)
def onboarding(payload: dict = Body(...)):
    conn = db.connect(get_db_path())
    try:
        return {"user_id": onboarding_service.save_onboarding(conn, payload)}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    finally:
        conn.close()


@app.get("/api/users/{user_id}/profile")
def profile(user_id: int):
    conn = db.connect(get_db_path())
    try:
        found = onboarding_service.load_profile(conn, user_id)
        if found is None:
            raise HTTPException(status_code=404, detail="User not found")
        return found
    finally:
        conn.close()


@app.post("/api/users/{user_id}/checkins", status_code=201)
def create_checkin(user_id: int, payload: dict = Body(...)):
    conn = db.connect(get_db_path())
    try:
        saved = checkin_service.save_checkin(conn, user_id, payload)
        recommendation_id = suggestion_service.generate_suggestion(
            conn, user_id, date.fromisoformat(saved["checkin_date"]))
        return {**saved, "recommendation_id": recommendation_id}
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except checkin_service.DuplicateCheckin as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    finally:
        conn.close()


@app.get("/api/users/{user_id}/suggestion")
def latest_suggestion(user_id: int):
    conn = db.connect(get_db_path())
    try:
        found = suggestion_service.latest_suggestion(conn, user_id)
        if found is None:
            raise HTTPException(status_code=404, detail="No suggestion yet")
        return found
    finally:
        conn.close()


@app.get("/api/demo/user")
def demo_user():
    """The simulated persona's user id (created on first use), so the screens can use the normal endpoints."""
    conn = db.connect(get_db_path())
    try:
        return {"user_id": demo_seed.seed_demo(conn)}
    finally:
        conn.close()

@app.post("/api/users/{user_id}/ask")
def ask(user_id: int, payload: dict = Body(...)):
    """Answer a free question. The AI is used only if the body says "consent_llm": true (strictly true, NFR-6)."""
    conn = db.connect(get_db_path())
    try:
        return ask_service.ask(conn, user_id, payload.get("question"), payload.get("consent_llm") is True,
                               llm_client.get_client())
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    finally:
        conn.close()
 

