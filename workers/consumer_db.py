import json
import os
from kafka import KafkaConsumer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import CheckResult, Monitor

consumer = KafkaConsumer(
    "health-results",
    bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id="db-writer",
    auto_offset_reset="earliest",
)

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

print("DB consumer listening...")
for message in consumer:
    event = message.value
    with Session() as session:
        monitor = (
            session.query(Monitor)
            .filter_by(url=event["url"])
            .first()
        )
        session.add(
            CheckResult(
                monitor_id=monitor.id if monitor else None,
                service=monitor.service if monitor else "unknown",
                endpoint=monitor.endpoint if monitor else event["url"],
                status="UP" if event["healthy"] else "DOWN",
                latency_ms=event["latency_ms"],
                checked_at=datetime.fromisoformat(event["timestamp"]),
            )
        )
        session.commit()
