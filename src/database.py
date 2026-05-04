import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, func
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, sessionmaker

from src.config import BASE_DIR

# Load environment variables from the root .env file
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Fetch the Postgres url from the .env file
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# If there is no DB connection string, terminate the app immediately
if not SQLALCHEMY_DATABASE_URL or not SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    print(
        "[-] CRITICAL ERROR: Valid PostgreSQL DATABASE_URL is missing in the .env file."
    )
    print("[!] Please create a .env file and add your PostgreSQL connection string:")
    print("    DATABASE_URL=postgresql://user:password@localhost:5432/dbname")
    sys.exit(1)

# PostgreSQL engine creation
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Incident(Base):
    __tablename__ = "incidents"

    # Mapped[тип] объясняет твоему Neovim, что тут лежит на самом деле
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_log: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    log_hash: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )

    occurrences: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    ai_log_review: Mapped[str | None] = mapped_column(Text, nullable=True)


Base.metadata.create_all(bind=engine)
