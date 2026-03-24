# SignalOps

SignalOps monitors backend microservice endpoints, publishes health checks to Kafka, stores results in TimescaleDB, exposes Prometheus metrics, and runs anomaly detection.

## Architecture
- Checker worker publishes events to Kafka
- Consumer DB stores events in TimescaleDB
- Consumer Prometheus exposes metrics on `/metrics`
- Consumer Anomaly detects latency anomalies (optional Slack alerting)
- FastAPI serves read APIs for the frontend

## Quick Start
1. Configure services in `signalops.yml`.
2. Set secrets in `.env`.
3. Start the stack:
   ```bash
   docker compose up --build -d
   ```
4. Run migration:
   ```bash
   docker compose run --rm consumer-db python migrate.py
   ```
5. Verify:
   ```bash
   curl http://localhost:8000/api/monitors
   curl http://localhost:8001/metrics | grep signalops
   ```

## Ports
- API: `8000`
- Prometheus exporter: `8001`
- Prometheus: `9090`
- Grafana: `3001`
- Kafka: `9092`

## Notes
- `.env` is ignored by git and should not be committed.
- If port `8000` is busy, update `docker-compose.yml` to use a different host port.
