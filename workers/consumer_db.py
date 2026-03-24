import json
import os
from kafka import KafkaConsumer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import CheckResult, Monitor

consumer = KafkaConsumer(
    "health.checks",
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
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
            .filter_by(service=event["service"], endpoint=event["endpoint"])
            .first()
        )
        session.add(
            CheckResult(
                monitor_id=monitor.id if monitor else None,
                service=event["service"],
                endpoint=event["endpoint"],
                status=event["status"],
                latency_ms=event["latency_ms"],
                checked_at=datetime.fromisoformat(event["timestamp"]),
            )
        )
        session.commit()
