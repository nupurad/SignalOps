import httpx
import json
import time
import yaml
import os
from kafka import KafkaProducer
from datetime import datetime, timezone
from pathlib import Path

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_serializer=lambda v: json.dumps(v).encode(),
)

STATE_DIR = Path(os.getenv("CHECKER_STATE_DIR", "/app/state"))
STATE_FILE = STATE_DIR / "last_checked.json"


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))

with open("/app/signalops.yml") as f:
    config = yaml.safe_load(f)

state = load_state()
now = time.time()

for service_name, service in config["services"].items():
    base_url = service["base_url"]
    for ep in service["endpoints"]:
        url = base_url + ep["path"]
        interval_minutes = ep.get("interval", 1)
        key = f"{service_name}:{ep.get('method', 'GET')}:{ep['path']}"
        last_checked = state.get(key, 0)
        if now - last_checked < interval_minutes * 60:
            continue

        start = time.time()
        try:
            r = httpx.request(ep.get("method", "GET"), url, timeout=10)
            status = "UP" if r.status_code < 400 else "DOWN"
        except Exception:
            status = "DOWN"
        latency = (time.time() - start) * 1000

        event = {
            "service": service_name,
            "endpoint": ep["path"],
            "url": url,
            "status": status,
            "latency_ms": round(latency, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        producer.send("health.checks", value=event)
        print(f"Published: {service_name}{ep['path']} -> {status}")

        state[key] = now

producer.flush()
save_state(state)
