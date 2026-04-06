import json
import os
import time
from confluent_kafka import Producer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
ENDPOINTS_FILE = os.getenv("ENDPOINTS_FILE", "/app/endpoints.json")
TOPIC = "endpoint-checks"


def resolve_env(value):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.getenv(env_key, "")
    return value


def resolve_config(obj):
    if isinstance(obj, dict):
        return {k: resolve_config(resolve_env(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_config(v) for v in obj]
    return resolve_env(obj)


def load_endpoints():
    with open(ENDPOINTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return resolve_config(data)


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}", flush=True)


def create_producer():
    # Idempotent producer settings
    return Producer(
        {
            "bootstrap.servers": KAFKA_BROKER,
            "enable.idempotence": True,
            "acks": "all",
            "retries": 5,
            "linger.ms": 5,
        }
    )


def main():
    print(
        f"Producer starting. Broker={KAFKA_BROKER} endpoints={ENDPOINTS_FILE}",
        flush=True,
    )

    producer = create_producer()

    while True:
        try:
            endpoints = load_endpoints()

            for ep in endpoints:
                ep_id = ep.get("id")
                url = ep.get("url")
                if not ep_id or not url:
                    continue
                payload = {
                    "id": ep_id,
                    "url": url,
                    "method": ep.get("method", "GET"),
                    "payload": ep.get("payload", None),
                    "expected_status": ep.get("expected_status", 200),
                    "auth": ep.get("auth", None),
                }
                producer.produce(
                    TOPIC,
                    key=ep_id.encode("utf-8"),
                    value=json.dumps(payload).encode("utf-8"),
                    on_delivery=delivery_report,
                )
                print(f"Produced: id={ep_id} url={url}", flush=True)

            producer.flush()

        except Exception as exc:
            print(f"Producer error: {exc}", flush=True)

        time.sleep(60)


if __name__ == "__main__":
    main()
