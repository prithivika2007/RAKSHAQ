from fastapi import FastAPI

import app.models  # noqa: F401 - registers models with Base.metadata
from app.database import Base, engine
from app.database import Base, engine, ensure_schema_updated

# Initialize database tables
# Initialize database tables and apply backward-compatible schema updates
Base.metadata.create_all(bind=engine)
ensure_schema_updated(engine)

app = FastAPI(
    title="RAKSHAQ - Women's Night-Shift Safety System API",
    description="Backend API for RAKSHAQ commute safety monitoring and alert management.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "healthy"}
