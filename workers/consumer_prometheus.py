import json
import os
from kafka import KafkaConsumer
from prometheus_client import Gauge, Histogram, Counter, start_http_server

endpoint_up = Gauge(
    "signalops_up",
    "1 if endpoint is UP, 0 if DOWN",
    ["service", "endpoint"],
)
latency_hist = Histogram(
    "signalops_latency_ms",
    "Response latency in milliseconds",
    ["service", "endpoint"],
    buckets=[50, 100, 200, 500, 1000, 2000],
)
checks_total = Counter(
    "signalops_checks_total",
    "Total health checks performed",
    ["service", "endpoint", "status"],
)

start_http_server(8001)
print("Prometheus metrics at :8001/metrics")

consumer = KafkaConsumer(
    "health.checks",
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id="prometheus-exporter",
)

for message in consumer:
    e = message.value
    labels = [e["service"], e["endpoint"]]
    endpoint_up.labels(*labels).set(1 if e["status"] == "UP" else 0)
    latency_hist.labels(*labels).observe(e["latency_ms"])
    checks_total.labels(*labels, e["status"]).inc()
