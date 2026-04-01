#!/bin/sh
set -e

KAFKA_BROKER=${KAFKA_BROKER:-kafka:9092}
HOST=$(echo "$KAFKA_BROKER" | cut -d: -f1)
PORT=$(echo "$KAFKA_BROKER" | cut -d: -f2)

# Wait for TCP socket to open
for i in $(seq 1 60); do
  if nc -z "$HOST" "$PORT" >/dev/null 2>&1; then
    echo "Kafka is reachable at $KAFKA_BROKER"
    exit 0
  fi
  echo "Waiting for Kafka at $KAFKA_BROKER... ($i)"
  sleep 2
 done

echo "Kafka not reachable after timeout"
exit 1
