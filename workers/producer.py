import json
import os
import time
from kafka import KafkaProducer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
ENDPOINTS_FILE = os.getenv("ENDPOINTS_FILE", "/app/endpoints.json")
TOPIC = "endpoint-checks"

def load_endpoints():
    with open(ENDPOINTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        enable_idempotence=True,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

def main():
    print(f"Producer starting. Broker={KAFKA_BROKER} endpoints={ENDPOINTS_FILE}", flush=True)
    
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
                producer.send(TOPIC, key=ep_id, value=payload)
                print(f"Produced: id={ep_id} url={url}", flush=True)

            producer.flush()

        except Exception as exc:
            print(f"Producer error: {exc}", flush=True)

        time.sleep(60)


if __name__ == "__main__":
    main()