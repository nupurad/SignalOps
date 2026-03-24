from fastapi import FastAPI, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
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


@app.on_event("startup")
def startup():
    with SessionLocal() as db:
        sync_config(db)


@app.get("/api/monitors")
def get_monitors(db: Session = Depends(get_db)):
    monitors = db.query(Monitor).filter_by(is_active=True).all()
    response = []
    for m in monitors:
        latest = (
            db.query(CheckResult)
            .filter_by(monitor_id=m.id)
            .order_by(CheckResult.checked_at.desc())
            .first()
        )
        response.append(
            {
                "id": m.id,
                "service": m.service,
                "endpoint": m.endpoint,
                "url": m.url,
                "method": m.method,
                "interval": m.interval,
                "is_active": m.is_active,
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
