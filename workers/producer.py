import json
import os
import time
from confluent_kafka import Producer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
ENDPOINTS_FILE = os.getenv("ENDPOINTS_FILE", "/app/endpoints.json")
TOPIC = "endpoint-checks"


def load_endpoints():
    with open(ENDPOINTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


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
                payload = {"id": ep_id, "url": url}
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
