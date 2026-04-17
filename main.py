from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Incident, SessionLocal


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
def post_log(log: LogRequest, db: Session = Depends(get_db)):
    new_incident = Incident(raw_log=log.raw_log)
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    return new_incident


# @app.delete("/api/logs")
# def delete_log(log: LogRequest, db: Session = Depends(get_db)):
#     incident = Incident(raw_log=log.raw_log)
#     db.delete(incident)
#     db.commit()
#     return {"ok": True}
