
"""RAKSHAQ FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 - register models with Base.metadata
from app.database import Base, engine, ensure_schema_updated
from app.routes.drivers import router as drivers_router
from app.routes.incidents import router as incidents_router
from app.routes.trips import router as trips_router

# Apply backward-compatible schema updates and create missing tables.
ensure_schema_updated(engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAKSHAQ — Women's Night-Shift Safety System API",
    description=(
        "Backend API for RAKSHAQ commute safety monitoring, "
        "silent duress detection and real-time alert management."
    ),
    version="0.6.0",
)

# CORS configuration for the dashboard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers.
app.include_router(trips_router)
app.include_router(incidents_router)
app.include_router(drivers_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": app.version}
