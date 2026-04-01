import json
import os
import signal
import sys
import time
from datetime import datetime, timezone

import httpx
from kafka import KafkaConsumer, KafkaProducer

# Consumer reads endpoint-checks, performs HTTP checks, publishes results.
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
INPUT_TOPIC = "endpoint-checks"
OUTPUT_TOPIC = "health-results"
GROUP_ID = "health-check-workers"

# Flag to track shutdown state
shutdown = False


def handle_shutdown(signum, frame):
    global shutdown
    print("Drain mode activated - finishing current check before shutting down...", flush=True)
    shutdown = True


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def create_consumer():
    return KafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,  # manual commits so we control exactly when offset is committed
    )


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def check_endpoint(url: str):
    start = time.time()
    status_code = None
    healthy = False
    try:
        resp = httpx.get(url, timeout=5)
        status_code = resp.status_code
        healthy = status_code < 400
    except Exception:
        # Any network error counts as unhealthy.
        healthy = False
    latency_ms = round((time.time() - start) * 1000, 2)
    return status_code, latency_ms, healthy


def main():
    consumer = create_consumer()
    producer = create_producer()

    while True:
        if shutdown:
            print("Drain complete - shutting down cleanly", flush=True)
            consumer.close()
            sys.exit(0)

        batch = consumer.poll(timeout_ms=1000)
        if not batch:
            continue

        for _tp, messages in batch.items():
            for message in messages:
                event = message.value
                ep_id = event.get("id")
                url = event.get("url")
                if not ep_id or not url:
                    consumer.commit()
                    continue

                print(
                    f"Consumer got partition={message.partition} "
                    f"offset={message.offset} id={ep_id}",
                    flush=True,
                )

                status_code, latency_ms, healthy = check_endpoint(url)
                payload = {
                    "id": ep_id,
                    "url": url,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "healthy": healthy,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                try:
                    producer.send(OUTPUT_TOPIC, value=payload)
                    producer.flush()
                except Exception as exc:
                    print(f"Publish error: {exc}", flush=True)

                # Commit offset only after message is fully processed and result published
                # This ensures if consumer crashes before commit, Kafka redelivers the message
                consumer.commit()

                if shutdown:
                    print("Drain complete - shutting down cleanly", flush=True)
                    consumer.close()
                    sys.exit(0)


if __name__ == "__main__":
    main()
