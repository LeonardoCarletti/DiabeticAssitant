# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, chat, logs, profile, workouts, vitals, nutrition

app = FastAPI(title="DiabeticAssistant API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(logs.router)
app.include_router(profile.router)
app.include_router(workouts.router)
app.include_router(vitals.router)
app.include_router(nutrition.router)

@app.get("/")
def root():
    return {"status": "ok", "service": "DiabeticAssistant API V3", "modules": ["auth", "chat", "logs", "profile", "workouts", "vitals", "nutrition"]}

@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0"}
