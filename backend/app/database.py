from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure the SQLite database file is stored inside the backend directory
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "rakshaq.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_updated(eng):
    """Safely updates existing SQLite tables with any newly added model columns.

    SQLAlchemy's create_all() does not alter existing tables. This function
    ensures backward compatibility without requiring external migration tooling.
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
                conn.execute(text("ALTER TABLE employees ADD COLUMN pin_locked_until DATETIME;"))
            conn.commit()


def get_db():
    """Dependency that yields a database session and ensures closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
