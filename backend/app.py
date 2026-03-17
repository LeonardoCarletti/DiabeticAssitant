import os
import random
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query
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

class PredictResponse(BaseModel):
    prediction: str
    confidence: float
    next_glucose: float
    trend: str

from typing import Literal

SourceType = Literal["manual", "cgm", "lab", "other"]
TrendType = Literal["falling", "rising", "stable", "unknown"]
ContextType = Literal["fasting", "pre_meal", "post_meal", "pre_workout", "post_workout", "bedtime", "random", "other"]

class GlucoseEventOut(BaseModel):
    id: str
    measured_at: str
    value_mg_dl: float
    trend: TrendType
    source: SourceType
    context: ContextType
    hypo_flag: bool
    hyper_flag: bool

class TimeInRangeMetrics(BaseModel):
    target_min_mg_dl: float
    target_max_mg_dl: float
    percent_in_range: float
    percent_below_range: float
    percent_above_range: float

class DistributionMetrics(BaseModel):
    manual_count: int
    cgm_count: int

class GlucoseMetrics(BaseModel):
    count_events: int
    avg_mg_dl: Optional[float]
    min_mg_dl: Optional[float]
    max_mg_dl: Optional[float]
    time_in_range: Optional[TimeInRangeMetrics]
    distribution: Optional[DistributionMetrics]

class GlucoseLogsResponse(BaseModel):
    range: str
    granularity: Literal["point", "hour", "day"]
    glucose_events: List[GlucoseEventOut]
    metrics: GlucoseMetrics

class GlucoseEventRequest(BaseModel):
    value_mg_dl: float
    measured_at: str
    source: Optional[str] = "manual"
    device_id: Optional[str] = None
    context: Optional[str] = "random"
    notes: Optional[str] = None
    correlation_id: Optional[str] = None


class MealItem(BaseModel):
    name: str
    carbs_g: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    portion: Optional[str] = None


class MealGlucoseLink(BaseModel):
    glucose_event_id: str
    relation: str


class MealRequest(BaseModel):
    name: str
    meal_type: Optional[str] = "other"
    eaten_at: str
    total_carbs_g: Optional[float] = None
    total_protein_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    estimated: Optional[bool] = True
    items: Optional[List[MealItem]] = []
    notes: Optional[str] = None
    linked_glucose_events: Optional[List[MealGlucoseLink]] = []

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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 1000, "temperature": 0.7}
        }
        for attempt in range(3):
            async with httpx.AsyncClient(timeout=25.0) as c:
                r = await c.post(url, json=payload)
            data = r.json()
            print(f"Gemini status: {r.status_code}, keys: {list(data.keys())}")
            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"Gemini 429 rate limit, aguardando {wait}s...")
                await asyncio.sleep(wait)
                continue
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            elif "error" in data:
                print(f"Gemini API error: {data['error']}")
                return ""
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
    system = "Voce e um assistente especialista em diabetes. Responda sempre em portugues de forma clara e util. Seja conciso e empatico."
    reply = await call_gemini(req.message, system)
    if reply:
        return ChatResponse(response=reply)
    return ChatResponse(response=f"[Demo] {random.choice(DIABETES_RESPONSES)}")

@app.post("/api/logs/glucose")
async def add_glucose_log(req: GlucoseEventRequest, creds: HTTPAuthorizationCredentials = Depends(security)):
    # Em um ambiente real, pegariamos o user_id do token (creds) e fariamos o INSERT no Supabase aqui
    # Mockando a resposta de sucesso conforme o payload do Perplexity
    import uuid
    from datetime import datetime
    
    return {
        "id": str(uuid.uuid4()),
        "user_id": "auth-user-uuid",
        "value_mg_dl": req.value_mg_dl,
        "trend": "stable",
        "source": req.source,
        "context": req.context,
        "hypo_flag": req.value_mg_dl < 70,
        "hyper_flag": req.value_mg_dl > 180,
        "measured_at": req.measured_at,
        "recorded_at": datetime.utcnow().isoformat(),
        "notes": req.notes,
        "correlation_id": req.correlation_id
    }


@app.post("/api/nutrition/meals")
async def add_meal_log(req: MealRequest, creds: HTTPAuthorizationCredentials = Depends(security)):
    import uuid
    from datetime import datetime
    
    return {
        "id": str(uuid.uuid4()),
        "user_id": "auth-user-uuid",
        "name": req.name,
        "meal_type": req.meal_type,
        "eaten_at": req.eaten_at,
        "total_carbs_g": req.total_carbs_g,
        "total_protein_g": req.total_protein_g,
        "total_fat_g": req.total_fat_g,
        "estimated": req.estimated,
        "notes": req.notes
    }


@app.get("/api/logs", response_model=GlucoseLogsResponse)
async def get_logs(
    range: Literal["6h", "24h", "7d", "30d"] = Query("6h"),
    source: Literal["manual", "cgm", "all"] = Query("all"),
    granularity: Literal["point", "hour", "day"] = Query("point"),
    creds: HTTPAuthorizationCredentials = Depends(security)
):
    import uuid
    now = datetime.utcnow()
    # Retornando o formato agregado sugerido pelo Perplexity
    events = []
    
    # Mocking data to represent an average CGM curve
    for i in range(24):
        val = random.randint(80, 160)
        events.append(GlucoseEventOut(
            id=str(uuid.uuid4()),
            measured_at=(now - timedelta(hours=i)).replace(microsecond=0).isoformat() + "-03:00",
            value_mg_dl=float(val),
            trend=random.choice(["falling", "rising", "stable"]),
            source="manual" if i % 4 == 0 else "cgm",
            context=random.choice(["fasting", "pre_meal", "post_meal", "random"]),
            hypo_flag=val < 70,
            hyper_flag=val > 180
        ))
        
    avg_val = sum(e.value_mg_dl for e in events) / len(events)
    min_val = min(e.value_mg_dl for e in events)
    max_val = max(e.value_mg_dl for e in events)
    
    in_range = sum(1 for e in events if 70 <= e.value_mg_dl <= 180)
    below = sum(1 for e in events if e.value_mg_dl < 70)
    above = sum(1 for e in events if e.value_mg_dl > 180)
    total = len(events) or 1

    metrics = GlucoseMetrics(
        count_events=len(events),
        avg_mg_dl=float(f"{avg_val:.1f}"),
        min_mg_dl=min_val,
        max_mg_dl=max_val,
        time_in_range=TimeInRangeMetrics(
            target_min_mg_dl=70.0,
            target_max_mg_dl=180.0,
            percent_in_range=float(f"{(in_range / total) * 100:.1f}"),
            percent_below_range=float(f"{(below / total) * 100:.1f}"),
            percent_above_range=float(f"{(above / total) * 100:.1f}")
        ),
        distribution=DistributionMetrics(
            manual_count=sum(1 for e in events if e.source == "manual"),
            cgm_count=sum(1 for e in events if e.source == "cgm")
        )
    )

    
    return GlucoseLogsResponse(
        range=range,
        granularity=granularity,
        glucose_events=events,
        metrics=metrics
    )


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
    system = "Personal trainer especialista em diabetes. Retorne APENAS JSON valido, sem texto extra, sem markdown, sem backticks."
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
    return {"status": "ok", "service": "DiabeticAssistant API", "version": "2.4-gemini-retry"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "ai": "gemini-2.0-flash"}
