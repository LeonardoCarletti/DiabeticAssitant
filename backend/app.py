import os
import random
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="DiabeticAssistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


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


class WorkoutProfile(BaseModel):
    goal: str
    level: str
    glucose: str
    age: Optional[int] = 30
    weight: Optional[float] = 70.0


class AuthRequest(BaseModel):
    phone: str


class VerifyRequest(BaseModel):
    phone: str
    code: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: Optional[str] = None


DIABETES_RESPONSES = [
    "Mantenha a glicemia entre 80-180 mg/dL durante exercicios.",
    "Beba agua regularmente para ajudar no controle glicemico.",
    "Monitore sua glicemia antes e apos as refeicoes.",
    "Exercicios aerobicos ajudam a reduzir a resistencia a insulina.",
    "Consulte seu medico antes de iniciar novos exercicios.",
    "Carboidratos complexos sao melhores para controle glicemico.",
    "O estresse pode elevar a glicemia - pratique relaxamento.",
    "Sono adequado e essencial para o controle do diabetes.",
]

WORKOUT_TEMPLATES = {
    "hipertrofia": [
        {"name": "Supino Reto", "sets": 4, "reps": "8-12", "rest": "90s", "notes": "Controle o movimento"},
        {"name": "Agachamento", "sets": 4, "reps": "8-10", "rest": "120s", "notes": "Profundidade completa"},
        {"name": "Remada Curvada", "sets": 3, "reps": "10-12", "rest": "90s", "notes": "Costas retas"},
        {"name": "Desenvolvimento", "sets": 3, "reps": "10-12", "rest": "60s", "notes": "Amplitude total"},
        {"name": "Rosca Direta", "sets": 3, "reps": "12-15", "rest": "60s", "notes": "Sem balanco"},
    ],
    "emagrecimento": [
        {"name": "Burpee", "sets": 4, "reps": "15", "rest": "60s", "notes": "Maximo de intensidade"},
        {"name": "Mountain Climber", "sets": 3, "reps": "20", "rest": "45s", "notes": "Core ativo"},
        {"name": "Agachamento Sumo", "sets": 4, "reps": "15", "rest": "60s", "notes": "Joelhos para fora"},
        {"name": "Polichinelo", "sets": 3, "reps": "30", "rest": "30s", "notes": "Ritmo constante"},
        {"name": "Prancha", "sets": 3, "reps": "45s", "rest": "30s", "notes": "Corpo alinhado"},
    ],
    "resistencia": [
        {"name": "Corrida Leve", "sets": 1, "reps": "20min", "rest": "0s", "notes": "Ritmo moderado"},
        {"name": "Ciclismo", "sets": 1, "reps": "15min", "rest": "0s", "notes": "Cadencia constante"},
        {"name": "Pulo Corda", "sets": 5, "reps": "2min", "rest": "30s", "notes": "Ritmo uniforme"},
        {"name": "Agachamento 20rep", "sets": 3, "reps": "20", "rest": "45s", "notes": "Sem parar"},
        {"name": "Flexao Continua", "sets": 3, "reps": "15-20", "rest": "45s", "notes": "Lento e controlado"},
    ],
}


async def call_gemini(prompt: str, system: str = "") -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("Gemini: no API key found")
        return ""
    try:
        import httpx
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 1000, "temperature": 0.7}
        }
        async with httpx.AsyncClient(timeout=25.0) as c:
            r = await c.post(url, json=payload)
            data = r.json()
            print(f"Gemini status: {r.status_code}, keys: {list(data.keys())}")
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            elif "error" in data:
                print(f"Gemini API error: {data['error']}")
            return ""
    except Exception as e:
        print(f"Gemini exception: {e}")
        return ""


@app.post("/api/auth/send-otp")
async def send_otp(req: AuthRequest):
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if supabase_url and supabase_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.post(
                    f"{supabase_url}/auth/v1/otp",
                    headers={"apikey": supabase_key, "Content-Type": "application/json"},
                    json={"phone": req.phone}
                )
                if r.status_code == 200:
                    return {"message": "OTP enviado", "demo": False}
        except Exception as e:
            print(f"Supabase OTP error: {e}")
    return {"message": "OTP enviado (demo: use 000000)", "demo": True}


@app.post("/api/auth/verify-otp", response_model=AuthResponse)
async def verify_otp(req: VerifyRequest):
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if supabase_url and supabase_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.post(
                    f"{supabase_url}/auth/v1/verify",
                    headers={"apikey": supabase_key, "Content-Type": "application/json"},
                    json={"phone": req.phone, "token": req.code, "type": "sms"}
                )
                if r.status_code == 200:
                    data = r.json()
                    return AuthResponse(
                        access_token=data.get("access_token", "demo-token"),
                        user_id=data.get("user", {}).get("id")
                    )
        except Exception as e:
            print(f"Supabase verify error: {e}")
    if req.code == "000000":
        return AuthResponse(access_token="demo-token-2024", user_id="demo-user")
    raise HTTPException(status_code=401, detail="Codigo invalido")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, creds: HTTPAuthorizationCredentials = Depends(security)):
    system = "Voce e um assistente especialista em diabetes. Responda sempre em portugues de forma clara e util. Seja conciso e empatiico."
    reply = await call_gemini(req.message, system)
    if reply:
        return ChatResponse(response=reply)
    return ChatResponse(response=f"[Demo] {random.choice(DIABETES_RESPONSES)}")


@app.get("/api/logs", response_model=List[LogEntry])
async def get_logs(creds: HTTPAuthorizationCredentials = Depends(security)):
    now = datetime.utcnow()
    return [
        LogEntry(
            id=i,
            timestamp=(now - timedelta(hours=i)).isoformat(),
            value=random.randint(80, 160),
            type="glucose"
        )
        for i in range(12)
    ]


@app.get("/api/predict", response_model=PredictResponse)
async def predict(creds: HTTPAuthorizationCredentials = Depends(security)):
    g = random.randint(100, 140)
    return PredictResponse(
        prediction=f"Glicemia projetada: {g + 5} mg/dL",
        confidence=0.85,
        next_glucose=g + 5,
        trend="estavel"
    )


@app.post("/api/workout/generate")
async def generate_workout(profile: WorkoutProfile, creds: HTTPAuthorizationCredentials = Depends(security)):
    glucose_val = int(profile.glucose) if profile.glucose.isdigit() else 120
    if glucose_val < 100:
        grec = f"Glicemia {glucose_val} mg/dL - consuma 15g de carbo antes de treinar."
    elif glucose_val > 250:
        grec = f"Glicemia {glucose_val} mg/dL - evite exercicio intenso. Consulte medico."
    else:
        grec = f"Glicemia {glucose_val} mg/dL - ideal para treino. Hidrate-se bem."
    system = "Personal trainer especialista em diabetes. Retorne APENAS JSON valido, sem texto extra, sem markdown, sem ```."
    prompt = (
        f"Crie um treino de {profile.goal} para nivel {profile.level}, "
        f"glicemia {profile.glucose} mg/dL, idade {profile.age}, peso {profile.weight}kg. "
        "Retorne APENAS JSON com: title, duration, level, glucose_recommendation, "
        "exercises (array com name/sets/reps/rest/notes), coach_tip."
    )
    reply = await call_gemini(prompt, system)
    if reply:
        try:
            clean = reply.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(clean)
        except Exception as e:
            print(f"Gemini workout JSON error: {e} | reply[:200]: {reply[:200]}")
    dur = {"iniciante": "40 min", "intermediario": "55 min", "avancado": "70 min"}
    exs = WORKOUT_TEMPLATES.get(profile.goal, WORKOUT_TEMPLATES["hipertrofia"])
    return {
        "title": f"Treino de {profile.goal.capitalize()} - {profile.level.capitalize()}",
        "duration": dur.get(profile.level, "55 min"),
        "level": profile.level,
        "glucose_recommendation": grec,
        "exercises": exs,
        "coach_tip": f"Para {profile.goal}: hidrate-se, monitore a glicemia e descanse adequadamente."
    }


@app.get("/")
async def root():
    return {"status": "ok", "service": "DiabeticAssistant API", "version": "2.2-gemini"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "ai": "gemini-1.5-flash"}
