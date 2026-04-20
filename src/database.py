import os

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

os.makedirs("data", exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///data/database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    raw_log = Column(Text, nullable=False)
    status = Column(String, default="pending")
    ai_summary = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)
