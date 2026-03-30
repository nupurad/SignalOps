from fastapi import FastAPI, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from pydantic import BaseModel
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker
from urllib.parse import urlparse
import json
import os

from config_loader import sync_config
from models import Monitor, CheckResult

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class MonitorCreate(BaseModel):
    service: str
    endpoint: str
    url: str
    method: str = "GET"
    interval: int = 1


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def load_endpoints():
    endpoints_file = os.getenv("ENDPOINTS_FILE", "/app/endpoints.json")
    with open(endpoints_file, "r", encoding="utf-8") as f:
        return json.load(f)

@app.on_event("startup")
def startup():
    with SessionLocal() as db:
        sync_config(db)


@app.get("/api/monitors")
def get_monitors(db: Session = Depends(get_db)):
    endpoints = load_endpoints()
    response = []
    for ep in endpoints:
        url = ep.get("url")
        ep_id = ep.get("id")
        if not url or not ep_id:
            continue

        parsed = urlparse(url)
        service = parsed.hostname or "external"
        endpoint_path = parsed.path or "/"

        latest = (
            db.query(CheckResult)
            .filter(
                or_(CheckResult.endpoint == endpoint_path, CheckResult.endpoint == url)
            )
            .order_by(CheckResult.checked_at.desc())
            .first()
        )

        response.append(
            {
                "id": ep_id,
                "service": service,
                "endpoint": endpoint_path,
                "url": url,
                "method": "GET",
                "interval": 1,
                "is_active": True,
                "status": latest.status if latest else None,
                "latency_ms": latest.latency_ms if latest else None,
                "checked_at": latest.checked_at if latest else None,
            }
        )

    return response


@app.get("/api/monitors/{monitor_id}/results")
def get_results(monitor_id: int, db: Session = Depends(get_db)):
    return (
        db.query(CheckResult)
        .filter_by(monitor_id=monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(60)
        .all()
    )


@app.post("/api/monitors")
@limiter.limit("10/minute")
def add_monitor(request: Request, data: MonitorCreate, db: Session = Depends(get_db)):
    monitor = Monitor(**data.dict())
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor
