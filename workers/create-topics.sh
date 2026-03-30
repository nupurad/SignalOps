#!/bin/sh
set -e

KAFKA_BROKER=${KAFKA_BROKER:-kafka:9092}

# Wait for Kafka to be ready
for i in $(seq 1 30); do
  if kafka-topics --bootstrap-server "$KAFKA_BROKER" --list >/dev/null 2>&1; then
    break
  fi
  echo "Waiting for Kafka... ($i)"
  sleep 2
done

kafka-topics --bootstrap-server "$KAFKA_BROKER" \
  --create --if-not-exists --topic endpoint-checks --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server "$KAFKA_BROKER" \
  --create --if-not-exists --topic health-results --partitions 3 --replication-factor 1

echo "Kafka topics ensured."
