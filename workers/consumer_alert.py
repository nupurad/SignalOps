import json
import os
import time
import requests
from kafka import KafkaConsumer

ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))

consumer = KafkaConsumer(
    "health.checks",
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id="down-alerts",
)

last_alert = {}


def should_alert(key: str, now: float) -> bool:
    last = last_alert.get(key, 0)
    return (now - last) >= ALERT_COOLDOWN_SECONDS


def send_alert(event):
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    text = (
        f"ALERT: {event['service']}{event['endpoint']} is DOWN "
        f"(latency={event.get('latency_ms', 'n/a')}ms)"
    )
    requests.post(webhook, json={"text": text}, timeout=10)


for message in consumer:
    event = message.value
    if event.get("status") != "DOWN":
        continue

    key = f"{event['service']}:{event['endpoint']}"
    now = time.time()
    if should_alert(key, now):
        send_alert(event)
        last_alert[key] = now
