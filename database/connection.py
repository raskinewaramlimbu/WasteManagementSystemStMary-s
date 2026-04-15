"""Database connection setup for SQLite via SQLAlchemy."""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "waste_services.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=False)


# Enable foreign key enforcement for SQLite
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session():
    return SessionLocal()


def init_db():
    """Create all tables if they don't already exist."""
    from database import models  # noqa: F401 – registers models with Base
    Base.metadata.create_all(bind=engine)
