import httpx
import json
import time
import yaml
import os
from kafka import KafkaProducer
from datetime import datetime, timezone

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_serializer=lambda v: json.dumps(v).encode(),
)

with open("/app/signalops.yml") as f:
    config = yaml.safe_load(f)

for service_name, service in config["services"].items():
    base_url = service["base_url"]
    for ep in service["endpoints"]:
        url = base_url + ep["path"]
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

producer.flush()
