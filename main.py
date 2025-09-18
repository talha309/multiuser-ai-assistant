from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from models import models
from database import database
from routes.auth import router as auth_router, get_current_user
from agent.chatbot import router as chat_router

# Create FastAPI app
app = FastAPI()

# Allow frontend (React) requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
models.Base.metadata.create_all(bind=database.engine)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {"msg": "Backend is running 🚀"}

# Middleware: DB healthcheck
@app.middleware("http")
async def db_healthcheck_middleware(request: Request, call_next):
    try:
        with database.SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        return PlainTextResponse("Database unavailable", status_code=503)
    return await call_next(request)

# Healthcheck endpoint
@app.get("/health")
def health():
    try:
        with database.SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

# ✅ Protected test route
@app.get("/auth/me")
def read_current_user(current_user=Depends(get_current_user)):
    return {
        "email": current_user.email,
        "id": current_user.id
    }
