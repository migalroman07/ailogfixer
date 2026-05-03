import os
import threading
import time
from datetime import datetime

from sqlalchemy.orm import Session

from src.ai_core import generate_solution
from src.collector import collect_logs
from src.config import load_config
from src.database import Incident, SessionLocal


def log_daemon(msg: str):
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("data/daemon.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def daemon_fixer(pending_logs, config, db: Session):
    for log in pending_logs:
        try:
            log.status = "processing"
            db.commit()
            log_daemon(f"Processing incident ID {log.id}")

            explanation, clean_commands = generate_solution(log.raw_log, config)
            if clean_commands and "MANUAL_INTERVENTION_REQUIRED" not in clean_commands:
                script_dir = os.path.join("data", "scripts")
                os.makedirs(script_dir, exist_ok=True)
                script_path = os.path.join(script_dir, f"fix_incident_{log.id}.sh")

                with open(script_path, "w", encoding="utf-8") as f:
                    if not clean_commands.startswith("#!"):
                        f.write("#!/bin/bash\n\n")
                    f.write(clean_commands)
                    f.write("\n")

                os.chmod(script_path, 0o755)
                log_daemon(f"Script saved: {script_path}")

            log.ai_summary = clean_commands
            log.ai_log_review = explanation

            log.status = "waiting"
            db.commit()
            log_daemon(f"Incident ID {log.id} is waiting for user execution.")

        except Exception as e:
            log_daemon(f"Error on Incident ID {log.id}: {e}")
            log.status = "pending"
            db.commit()


def daemon_worker():
    log_daemon("Daemon started working...")
    last_run_time = 0

    while True:
        try:
            config = load_config()
            interval = config.get("system", {}).get("interval", 30)

            if interval > 0:
                current_time = time.time()

                if current_time - last_run_time >= interval * 60:
                    collect_logs()
                    db: Session = SessionLocal()
                    try:
                        pending_logs = (
                            db.query(Incident)
                            .filter(Incident.status == "pending")
                            .all()
                        )

                        if pending_logs:
                            daemon_fixer(pending_logs, config, db)
                        else:
                            pass
                    except Exception as e:
                        log_daemon(f"Database error in daemon: {e}")
                    finally:
                        db.close()

                    last_run_time = time.time()

        except Exception as e:
            log_daemon(f"Daemon error: {e}")

        time.sleep(5)


def start_daemon():
    daemon_worker()


if __name__ == "__main__":
    start_daemon()
