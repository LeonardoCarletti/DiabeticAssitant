"""Vercel serverless entry point - Diabetic Assistant Backend.
App FastAPI minimo com routes essenciais sem dependencias pesadas.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth_routes import router as auth_router

app = FastAPI(
    title="Diabetic Assistant API",
    description="API for the Personal Diabetics Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# auth_routes.py ja define prefix="/auth" internamente
app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "ok", "service": "Diabetic Assistant API"}

@app.get("/health")
def health():
    return {"status": "healthy"}
