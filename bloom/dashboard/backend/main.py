"""
SSH Behaviors Evaluation Dashboard - FastAPI Backend

Run with:
    uvicorn dashboard.backend.main:app --reload --port 8000

Or from bloom directory:
    cd bloom && python -m uvicorn dashboard.backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .routes import status, behaviors, conversations, control, history

# Create app
app = FastAPI(
    title="SSH Behaviors Dashboard",
    description="Dashboard API for SSH Behaviors Evaluation Results",
    version="1.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(status.router)
app.include_router(behaviors.router)
app.include_router(conversations.router)
app.include_router(control.router)
app.include_router(history.router)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "SSH Behaviors Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/api/status",
            "stats": "/api/status/stats",
            "behaviors": "/api/behaviors",
            "conversations": "/api/conversations",
            "control": "/api/control",
            "history": "/api/history",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

