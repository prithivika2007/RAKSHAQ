import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

# Local fallback: SQLite file inside the backend directory
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "rakshaq.db"

# On Vercel/Render set DATABASE_URL (Neon/Supabase Postgres)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE}")

# Some providers give postgres:// but SQLAlchemy needs postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # NullPool = no stale connections in serverless; pre_ping for Neon sleeping
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Postgres has no DATETIME type, it uses TIMESTAMP
DT = "DATETIME" if IS_SQLITE else "TIMESTAMP"


def ensure_schema_updated(eng):
    """Safely updates existing tables with any newly added model columns.

    SQLAlchemy's create_all() does not alter existing tables. This function
    ensures backward compatibility without requiring external migration tooling.
    Works on both SQLite and Postgres.
    """
    with eng.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        if "employees" in tables:
            emp_cols = {c["name"] for c in inspector.get_columns("employees")}
            if "normal_pin_hash" not in emp_cols:
                conn.execute(text("ALTER TABLE employees ADD COLUMN normal_pin_hash VARCHAR(255);"))
            if "duress_pin_hash" not in emp_cols:
                conn.execute(text("ALTER TABLE employees ADD COLUMN duress_pin_hash VARCHAR(255);"))
            if "failed_pin_attempts" not in emp_cols:
                conn.execute(
                    text("ALTER TABLE employees ADD COLUMN failed_pin_attempts INTEGER NOT NULL DEFAULT 0;")
                )
            if "pin_locked_until" not in emp_cols:
                conn.execute(text(f"ALTER TABLE employees ADD COLUMN pin_locked_until {DT};"))
            conn.commit()
        if "trips" in tables:
            trip_cols = {c["name"] for c in inspector.get_columns("trips")}
            if "last_checkin_at" not in trip_cols:
                conn.execute(text(f"ALTER TABLE trips ADD COLUMN last_checkin_at {DT};"))
                conn.commit()


def get_db():
    """Dependency that yields a database session and ensures closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
