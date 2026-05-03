import hashlib
import re
import subprocess

from src.ai_core import generate_log_desc
from src.config import load_config
from src.database import Incident, SessionLocal


def collect_logs():
    config = load_config()
    INTERVAL = config["system"]["interval"]

    cmd = ["journalctl", "-p", "3", "--since", f"{INTERVAL} minutes ago", "--no-pager"]
    log = subprocess.run(cmd, capture_output=True, text=True).stdout

    if not log or "No entries" in log:
        return

    db = SessionLocal()
    try:
        log_hash = generate_log_hash(log.strip())

        existing_incident = (
            db.query(Incident)
            .filter(
                Incident.log_hash == log_hash,
                Incident.status.in_(["pending", "processing", "waiting"]),
            )
            .first()
        )

        if existing_incident:
            existing_incident.occurrences += 1
            db.commit()
            db.refresh(existing_incident)
            return
        else:
            new_incident = Incident(
                raw_log=log,
                status="pending",
                log_hash=log_hash,
                ai_log_review=generate_log_desc(log, config),
            )

            db.add(new_incident)
            db.commit()
            db.refresh(new_incident)

    finally:
        db.close()


def generate_log_hash(log_text: str) -> str:
    # Delete the timestamps like Apr dd hh:mm:ss
    clean_log = re.sub(r"^[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+", "", log_text)

    # delete process' PID
    clean_log = re.sub(r"\[\d+\]:", ":", clean_log)

    return hashlib.sha256(clean_log.encode("utf-8")).hexdigest()
