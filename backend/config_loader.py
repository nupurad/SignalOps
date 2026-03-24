import yaml
from sqlalchemy.orm import Session
from models import Monitor


def sync_config(db: Session) -> None:
    with open("/app/signalops.yml") as f:
        config = yaml.safe_load(f)

    # Deactivate all existing monitors first
    db.query(Monitor).update({Monitor.is_active: False})

    for service_name, service in config["services"].items():
        base_url = service["base_url"]
        for ep in service["endpoints"]:
            url = base_url + ep["path"]
            monitor = db.query(Monitor).filter_by(
                service=service_name, endpoint=ep["path"]
            ).first()
            if not monitor:
                monitor = Monitor(
                    service=service_name,
                    endpoint=ep["path"],
                    url=url,
                    method=ep.get("method", "GET"),
                    interval=ep.get("interval", 1),
                )
                db.add(monitor)
            else:
                monitor.url = url
                monitor.method = ep.get("method", "GET")
                monitor.interval = ep.get("interval", 1)
            monitor.is_active = True

    db.commit()
    print("Config synced from signalops.yml")
