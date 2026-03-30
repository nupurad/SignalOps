import json
import os
from kafka import KafkaConsumer
from prometheus_client import Gauge, Histogram, Counter, start_http_server

endpoint_up = Gauge(
    "signalops_up",
    "1 if endpoint is healthy, 0 if unhealthy",
    ["endpoint_id", "url"],
)
latency_hist = Histogram(
    "signalops_latency_ms",
    "Response latency in milliseconds",
    ["endpoint_id", "url"],
    buckets=[50, 100, 200, 500, 1000, 2000],
)
checks_total = Counter(
    "signalops_checks_total",
    "Total health checks performed",
    ["endpoint_id", "url", "healthy"],
)

start_http_server(8001)
print("Prometheus metrics at :8001/metrics")

consumer = KafkaConsumer(
    "health-results",
    bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id="prometheus-exporter",
)

for message in consumer:
    e = message.value
    labels = [e["id"], e["url"]]
    endpoint_up.labels(*labels).set(1 if e["healthy"] else 0)
    latency_hist.labels(*labels).observe(e["latency_ms"])
    checks_total.labels(*labels, str(e["healthy"])).inc()
