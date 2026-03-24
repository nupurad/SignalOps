import json
import os
import requests
from kafka import KafkaConsumer
from sklearn.ensemble import IsolationForest
from collections import defaultdict, deque
import numpy as np
import statistics

windows = defaultdict(lambda: deque(maxlen=120))
models = {}

consumer = KafkaConsumer(
    "health.checks",
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id="anomaly-detector",
)


def check_zscore(key, latency):
    window = windows[key]
    window.append(latency)
    if len(window) < 10:
        return False, 0
    mean = statistics.mean(window)
    stdev = statistics.stdev(window)
    if stdev == 0:
        return False, 0
    z = abs((latency - mean) / stdev)
    return z > 3, round(z, 2)


def get_model(key, window):
    if key not in models or len(window) % 60 == 0:
        X = np.array(list(window)).reshape(-1, 1)
        models[key] = IsolationForest(
            contamination=0.05,
            random_state=42,
        ).fit(X)
    return models[key]


def send_alert(event, latency, score):
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    requests.post(
        webhook,
        json={
            "text": (
                f"ALERT: {event['service']}{event['endpoint']} "
                f"latency={latency}ms (score={score:.2f})"
            )
        },
        timeout=10,
    )


for message in consumer:
    e = message.value
    key = f"{e['service']}{e['endpoint']}"
    latency = e["latency_ms"]
    windows[key].append(latency)

    if len(windows[key]) >= 20:
        model = get_model(key, windows[key])
        score = model.decision_function([[latency]])[0]
        pred = model.predict([[latency]])[0]
        if pred == -1:
            print(f"ANOMALY DETECTED: {key} latency={latency}ms")
            send_alert(e, latency, score)
