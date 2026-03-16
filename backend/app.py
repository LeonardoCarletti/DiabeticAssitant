"""Vercel serverless entry point - Diabetic Assistant Backend.
App FastAPI minimo com routes essenciais sem dependencias pesadas.
Incui: auth (OTP), chat (OpenAI com fallback), logs e predict.
"""
import os
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
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

security = HTTPBearer(auto_error=False)

# ──────────────────────────────────────────
# Modelos
# ──────────────────────────────────────────

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

# ──────────────────────────────────────────
# Endpoints utilitarios
# ──────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Diabetic Assistant API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ──────────────────────────────────────────
# /api/chat - LabMode Chat com IA
# ──────────────────────────────────────────

DIABETES_RESPONSES = [
    "Sua glicemia de 120 mg/dL esta dentro do range ideal (80-150). Continue monitorando apos as refeicoes.",
    "Para diabeticos tipo 1, o ideal e medir a glicemia antes e 2h apos cada refeicao principal.",
    "A atividade fisica aerobica tende a reduzir a glicemia. Sempre monitore antes e durante o exercicio.",
    "Carboidratos de alto indice glicemico elevam a glicemia rapidamente. Prefira carboidratos complexos.",
    "O estresse pode elevar a glicemia. Tecnicas de respiracao e mindfulness ajudam no controle.",
    "Hipoglicemia (abaixo de 70 mg/dL): consuma 15g de carboidrato de rapida absorcao imediatamente.",
    "Hiperglicemia acima de 250 mg/dL requer atencao medica. Hidratacao e ajuste de insulina sao essenciais.",
    "O sono de qualidade influencia diretamente a sensibilidade a insulina e o controle glicemico.",
    "Registrar refeicoes, doses de insulina e glicemias ajuda a identificar padroes e otimizar o controle.",
    "A hemoglobina glicada (HbA1c) reflete o controle medio dos ultimos 3 meses. O alvo usual e abaixo de 7%.",
]

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_researcher(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Chat com o assistente de diabetes. Usa OpenAI se configurado, caso contrario retorna resposta educativa."""
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
                            {"role": "system", "content": "Voce e um assistente especializado em diabetes. Responda em portugues brasileiro de forma clara, objetiva e empatica. Baseie suas respostas em evidencias medicas atuais. Nunca substitua orientacao medica profissional."},
                            {"role": "user", "content": request.message}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                data = resp.json()
                ai_response = data["choices"][0]["message"]["content"]
                return ChatResponse(response=ai_response)
        except Exception:
            pass

    # Fallback: resposta educativa baseada em keywords
    msg_lower = request.message.lower()
    if any(w in msg_lower for w in ["hipoglicemia", "baixa", "baixo", "70"]):
        response = DIABETES_RESPONSES[5]
    elif any(w in msg_lower for w in ["hiperglicemia", "alta", "alto", "250", "300"]):
        response = DIABETES_RESPONSES[6]
    elif any(w in msg_lower for w in ["exercicio", "treino", "academia", "corrida"]):
        response = DIABETES_RESPONSES[3]
    elif any(w in msg_lower for w in ["insulina", "dose", "basal", "bolus"]):
        response = DIABETES_RESPONSES[1]
    elif any(w in msg_lower for w in ["hba1c", "hemoglobina", "glicada"]):
        response = DIABETES_RESPONSES[9]
    elif any(w in msg_lower for w in ["sono", "dormir", "descanso"]):
        response = DIABETES_RESPONSES[7]
    elif any(w in msg_lower for w in ["carboidrato", "carbo", "comida", "refeicao"]):
        response = DIABETES_RESPONSES[3]
    else:
        response = random.choice(DIABETES_RESPONSES)

    return ChatResponse(response=f"[Modo Demo] {response}")

# ──────────────────────────────────────────
# /api/logs - Historico de glicemia
# ──────────────────────────────────────────

@app.get("/api/logs", response_model=list[LogEntry])
async def get_logs(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Retorna historico de registros de glicemia. Mock para demo."""
    now = datetime.utcnow()
    logs = []
    base_glucose = 110
    for i in range(24):
        ts = now - timedelta(hours=i)
        variation = random.randint(-30, 40)
        logs.append(LogEntry(
            id=i + 1,
            timestamp=ts.isoformat(),
            value=max(60, min(300, base_glucose + variation)),
            type="glucose"
        ))
    return logs

# ──────────────────────────────────────────
# /api/predict - Analise preditiva
# ──────────────────────────────────────────

@app.get("/api/predict", response_model=PredictResponse)
async def get_predictive_analysis(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Analise preditiva da glicemia. Mock para demo."""
    current = random.randint(90, 140)
    next_g = current + random.randint(-15, 25)
    trend = "estavel"
    if next_g > current + 10:
        trend = "subindo"
    elif next_g < current - 10:
        trend = "descendo"

    return PredictResponse(
        prediction=f"Glicemia projetada para proxima hora: {next_g} mg/dL",
        confidence=round(random.uniform(0.72, 0.91), 2),
        next_glucose=next_g,
        trend=trend
    )
