from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 - registers models with Base.metadata
from app.database import Base, engine, ensure_schema_updated
from app.routes.drivers import router as drivers_router
from app.routes.employees import router as employees_router
from app.routes.incidents import router as incidents_router
from app.routes.trips import router as trips_router

# Initialize database tables and apply backward-compatible schema updates
Base.metadata.create_all(bind=engine)
ensure_schema_updated(engine)

app = FastAPI(
    title="RAKSHAQ - Women's Night-Shift Safety System API",
    description="Backend API for RAKSHAQ commute safety monitoring and alert management.",
    version="0.1.0",
)

# Allow the local employee portal and security dashboard to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees_router)
app.include_router(trips_router)
app.include_router(incidents_router)
app.include_router(drivers_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "healthy"}