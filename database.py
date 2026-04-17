import datetime as dt

from sqlalchemy import JSON, DateTime, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine(
    "postgresql+psycopg://postgres:postgres@localhost:5432/ailogs",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    raw_log: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending")

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.UTC)
    )

    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_commands: Mapped[list | None] = mapped_column(JSON, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database was created")


if __name__ == "__main__":
    init_db()
