from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from routes.auth import router as auth_router
from database.database import Base, engine, SessionLocal
from models import models
from sqlalchemy import text

app = FastAPI()

# CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)

@app.get("/")
def root():
    return {"msg": "Auth system working 🚀"}

@app.middleware("http")
async def db_healthcheck_middleware(request: Request, call_next):
    try:
        # lightweight connection test
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        return PlainTextResponse("Database unavailable", status_code=503)
    return await call_next(request)

@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
 