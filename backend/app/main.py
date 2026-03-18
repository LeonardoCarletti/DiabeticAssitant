# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, chat, logs, profile

app = FastAPI(title="DiabeticAssistant API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restringir para domínio do frontend em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(logs.router)
app.include_router(profile.router)

@app.get("/")
def root():
    return {"status": "ok", "service": "DiabeticAssistant API V2"}

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
