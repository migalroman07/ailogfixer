from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ailogs"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    raw_log = Column(Text, nullable=False)
    status = Column(String, default="pending")
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    log_hash = Column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )
    occurrences = Column(Integer, default=1)


Base.metadata.create_all(bind=engine)
