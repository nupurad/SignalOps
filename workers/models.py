from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Monitor(Base):
    __tablename__ = "monitors"
    id = Column(Integer, primary_key=True)
    service = Column(String)
    endpoint = Column(String)
    url = Column(String)
    method = Column(String, default="GET")
    interval = Column(Integer)
    is_active = Column(Boolean, default=True)


class CheckResult(Base):
    __tablename__ = "check_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    monitor_id = Column(Integer, nullable=True)
    service = Column(String)
    endpoint = Column(String)
    status = Column(String)
    latency_ms = Column(Float)
    checked_at = Column(DateTime, primary_key=True)
