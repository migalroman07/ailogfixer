import hashlib

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import Incident, SessionLocal


class LogRequest(BaseModel):
    raw_log: str


app = FastAPI()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/api/logs")
def get_logs(db: Session = Depends(get_db), limit: int = 50):
    return db.scalars(select(Incident).limit(limit))


@app.post("/api/logs")
def post_log(log, db: Session = Depends(get_db)):
    log_hash = hashlib.sha256(log.raw_log.strip().encode("utf-8")).hexdigest()

    existing_incident = (
        db.query(Incident)
        .filter(Incident.log_hash == log_hash, Incident.status == "pending")
        .first()
    )

    if existing_incident:
        existing_incident.occurrences += 1
        db.commit()
        db.refresh(existing_incident)
        return {
            "status": "duplicate_updated",
            "incident_id": existing_incident.id,
            "occurrences": existing_incident.occurrences,
        }

    new_incident = Incident(
        raw_log=log.raw_log,
        status="pending",
        log_hash=log_hash,
    )

    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    return {"status": "sucess", "incident_id": new_incident.id}
