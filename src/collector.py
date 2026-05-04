import hashlib
import json
import re
import subprocess
from collections import defaultdict

from src.ai_core import generate_log_desc
from src.config import load_config
from src.database import Incident, SessionLocal


def collect_logs(custom_since: str = ""):
    """Fetches system logs line-by-line in JSON format and groups them by service."""
    config = load_config()
    interval = config["system"]["interval"]

    cmd = ["journalctl", "-p", "3", "-o", "json"]

    if custom_since == "boot":
        cmd.append("-b")
    elif custom_since:
        cmd.extend(["--since", custom_since])
    elif interval > 0:
        cmd.extend(["--since", f"{interval} minutes ago"])
    else:
        cmd.extend(["--since", "24 hours ago"])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not result.stdout or not result.stdout.strip():
        return

    # Group logs by their source service
    incidents_by_service = defaultdict(list)

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            entry = json.loads(line)
            service = (
                entry.get("_SYSTEMD_UNIT") or entry.get("SYSLOG_IDENTIFIER") or "system"
            )
            msg = entry.get("MESSAGE", "")

            if isinstance(msg, list):
                msg = bytes(msg).decode("utf-8", errors="replace")
            else:
                msg = str(msg)

            if msg:
                incidents_by_service[service].append(msg)

        except json.JSONDecodeError:
            continue

    if not incidents_by_service:
        return

    db = SessionLocal()
    try:
        for service, msgs in incidents_by_service.items():
            # Combine messages for context, keeping last 50 lines
            combined_msgs = "\n".join(msgs[-50:])
            formatted_log = f"[Service: {service}]\n{combined_msgs}"

            log_hash = generate_log_hash(formatted_log)

            existing_incident = (
                db.query(Incident)
                .filter(
                    Incident.log_hash == log_hash,
                    Incident.status.in_(["pending", "processing", "waiting"]),
                )
                .first()
            )

            if existing_incident:
                # Add the number of new errors to occurrences
                existing_incident.occurrences += len(msgs)
                db.commit()
                db.refresh(existing_incident)
            else:
                new_incident = Incident(
                    raw_log=formatted_log,
                    status="pending",
                    log_hash=log_hash,
                    ai_log_review=generate_log_desc(formatted_log, config),
                )

                db.add(new_incident)
                db.commit()
                db.refresh(new_incident)

    finally:
        db.close()


def generate_log_hash(log_text: str) -> str:
    # Remove dates/timestamps
    clean_log = re.sub(
        r"^[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+", "", log_text, flags=re.MULTILINE
    )
    # Remove PIDs
    clean_log = re.sub(r"\[\d+\]:", ":", clean_log)
    return hashlib.sha256(clean_log.encode("utf-8")).hexdigest()
