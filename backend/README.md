# RAKSHAQ - Backend

Backend service for **RAKSHAQ: Women's Night-Shift Safety System**, handling commute monitoring, verification, alert management, and safe arrival tracking.

## Tech Stack
- **Framework:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Language:** Python 3.10+

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py         # Application entrypoint & health check endpoint
│   ├── database.py     # SQLite connection & SQLAlchemy Base/Session setup
│   ├── models/         # SQLAlchemy database models
│   ├── schemas/        # Pydantic schemas for request/response validation
│   ├── routes/         # API endpoint routers
│   ├── services/       # Business logic and alert management services
│   └── ml/             # Internal ML inference adapters
├── requirements.txt    # Backend dependencies
└── README.md           # Documentation and run instructions
```

## Getting Started

### 1. Create and Activate Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

### 4. Verify Health Check
Test the health endpoint via `curl` or your browser:
```bash
curl http://127.0.0.1:8000/health
```
Expected response:
```json
{"status": "healthy"}
```

Interactive documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

