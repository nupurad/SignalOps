# SignalOps

SignalOps is a distributed health-check pipeline for backend endpoints. A producer publishes endpoint tasks to Kafka, multiple consumers perform checks in parallel, and downstream processors store results in TimescaleDB, expose Prometheus metrics, and trigger Slack alerts.

## Architecture
- Producer (`producer.py`) reads `endpoints.json` and publishes tasks to Kafka topic `endpoint-checks`
- Consumers (`consumer.py`, 3 instances) share `group_id=health-check-workers` and process partitions in parallel
- Results are published to Kafka topic `health-results`
- Result processors:
  - `consumer_db.py` writes to TimescaleDB
  - `consumer_prometheus.py` exposes `/metrics` for Prometheus
  - `consumer_anomaly.py` runs anomaly detection 
  - `consumer_alert.py` posts Slack alerts for DOWN endpoints
- FastAPI reads `endpoints.json` and returns latest results from TimescaleDB
- Next.js frontend displays `/api/monitors`

## Configuration
- `endpoints.json`: list of endpoint objects `{ id, url }`
- `.env`: database credentials, Kafka broker, Slack webhook, alert cooldown

## Quick Start
1. Configure `endpoints.json`.
2. Set secrets in `.env`.
3. Start the stack:
   ```bash
   docker compose up --build -d
   ```
4. Run migration (first run only):
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
- Frontend (Next.js): `3000`
- Prometheus exporter: `8001`
- Prometheus: `9090`
- Grafana: `3001`
- Kafka: `9092`

## Notes
- `.env` is ignored by git and should not be committed.
- Kafka topics are created by `kafka-init` on startup:
  - `endpoint-checks` (3 partitions)
  - `health-results` (3 partitions)
- If port `8000` is busy, update `docker-compose.yml` to use a different host port.
