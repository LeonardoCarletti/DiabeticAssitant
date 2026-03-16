"""Vercel serverless entry point - Diabetic Assistant Backend.
App FastAPI consolidado com routes: auth, chat, workouts, logs e predict.
"""
import os
import sys
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Add current dir to sys.path to allow imports from api.*
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.auth_routes import router as auth_router

app = FastAPI(
    title="Diabetic Assistant API",
    description="API for the Personal Diabetics Assistant",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(auth_router)

# Import workout router with safety check for dependencies
try:
    from api.workout_routes import router as workout_router
    app.include_router(workout_router)
except Exception as e:
    print(f"Warning: Could not load workout_router: {e}")

security = HTTPBearer(auto_error=False)

# ── Models ────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class LogEntry(BaseModel):
    id: int
    timestamp: str
    value: float
    type: str

class PredictResponse(BaseModel):
    prediction: str
    confidence: float
    next_glucose: float
    trend: str

# ── Endpoints ────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "service": "Diabetic Assistant API", "version": "1.1.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ── /api/chat ────────────────────────────────────────────────────
DIABETES_RESPONSES = [
    "Sua glicemia de 120 mg/dL esta dentro do range ideal (80-150).",
    "Para diabeticos tipo 1, o ideal e medir a glicemia antes e 2h apos cada refeicao.",
    "A atividade fisica aerobica tende a reduzir a glicemia.",
    "Carboidratos de alto indice glicemico elevam a glicemia rapidamente.",
    "O estresse pode elevar a glicemia via cortisol.",
    "Hipoglicemia (abaixo de 70 mg/dL): use a regra dos 15g de carbo.",
    "Hiperglicemia acima de 250 mg/dL requer atencao redobrada.",
    "O sono de qualidade influencia a sensibilidade a insulina.",
    "A hemoglobina glicada (HbA1c) reflete o controle dos ultimos 3 meses.",
]

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_researcher(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "Voce e um assistente especializado em diabetes e treinos. Responda em PT-BR de forma clara e empatica."},
                            {"role": "user", "content": request.message}
                        ],
                        "max_tokens": 500
                    }
                )
                data = resp.json()
                return ChatResponse(response=data["choices"][0]["message"]["content"])
        except Exception:
            pass
    
    # Fallback
    return ChatResponse(response=f"[Modo Demo] {random.choice(DIABETES_RESPONSES)}")

# ── /api/logs ────────────────────────────────────────────────────
@app.get("/api/logs", response_model=list[LogEntry])
async def get_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Mock data - Real integration with Supabase needed in separate service
    now = datetime.utcnow()
    logs = [
        LogEntry(id=i, timestamp=(now - timedelta(hours=i)).isoformat(), 
                 value=random.randint(80, 160), type="glucose")
        for i in range(12)
    ]
    return logs

# ── /api/predict ─────────────────────────────────────────────────
@app.get("/api/predict", response_model=PredictResponse)
async def get_predictive_analysis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    current = random.randint(100, 140)
    return PredictResponse(
        prediction=f"Glicemia projetada: {current + 5} mg/dL",
        confidence=0.85,
        next_glucose=current + 5,
        trend="estavel"
    )
