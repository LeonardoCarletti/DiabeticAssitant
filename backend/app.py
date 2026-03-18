import os
import random
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Literal

from backend.schemas import (
    GlucoseEventCreate, GlucoseEventOut, GlucoseLogsResponse,
    GlucoseMetrics, TimeInRangeMetrics, DistributionMetrics,
    MealCreateRequest, MealOut, MealItemOut, MealsListResponse,
)
from backend.utils import compute_time_in_range, get_start_time, is_emergency, EMERGENCY_RESPONSE, build_clinical_context
from backend.prompts import build_full_system_prompt

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from statistics import mean as stat_mean
import uuid

from backend.database import get_db
from backend.models import GlucoseEvent, Meal, MealItem, MealGlucoseLink
from backend.auth import get_current_user
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
    current_glucose: Optional[float] = None

class ChatResponse(BaseModel):
    reply: str
    is_emergency: bool

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

async def call_gemini(prompt: str, system: str = "", temperature: float = 0.7) -> str:
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
            "generationConfig": {"maxOutputTokens": 1000, "temperature": temperature}
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
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1) Safe Guard — verificar emergência ANTES de qualquer chamada à IA
    if is_emergency(payload.message, payload.current_glucose):
        return ChatResponse(reply=EMERGENCY_RESPONSE, is_emergency=True)

    # 2) Buscar contexto clínico real do banco (últimas 24h)
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    glucose_res = await db.execute(
        select(GlucoseEvent).where(
            and_(
                GlucoseEvent.user_id == current_user.id,
                GlucoseEvent.measured_at >= since_24h,
            )
        ).order_by(GlucoseEvent.measured_at.desc())
    )
    glucose_events = glucose_res.scalars().all()

    meals_res = await db.execute(
        select(Meal).where(
            and_(
                Meal.user_id == current_user.id,
                Meal.eaten_at >= since_24h,
            )
        ).order_by(Meal.eaten_at.desc())
    )
    meals = meals_res.scalars().all()

    # 3) Converter para dicts simples para as funções de utils
    events_dicts = [
        {"value_mg_dl": float(e.value_mg_dl), "source": e.source}
        for e in glucose_events
    ]
    meals_dicts = [
        {
            "name":            m.name,
            "meal_type":       m.meal_type,
            "eaten_at":        m.eaten_at.isoformat(),
            "total_carbs_g":   float(m.total_carbs_g)   if m.total_carbs_g   else 0,
            "total_protein_g": float(m.total_protein_g) if m.total_protein_g else 0,
            "total_fat_g":     float(m.total_fat_g)     if m.total_fat_g     else 0,
        }
        for m in meals
    ]

    # 4) Montar contexto clínico + system prompt completo
    clinical_ctx  = build_clinical_context(events_dicts, meals_dicts, payload.current_glucose)
    system_prompt = build_full_system_prompt(clinical_ctx)

    # 5) Chamar Gemini 2.0 Flash
    reply = await call_gemini(payload.message, system_prompt, temperature=0.4)
    if reply:
        return ChatResponse(reply=reply, is_emergency=False)
    
    return ChatResponse(reply="Desculpe, não consegui processar a resposta agora.", is_emergency=False)

@app.post("/api/logs/glucose", response_model=GlucoseEventOut, status_code=201)
async def create_glucose_event(
    payload: GlucoseEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    event = GlucoseEvent(
        user_id=current_user.id,
        value_mg_dl=payload.value_mg_dl,
        measured_at=payload.measured_at,
        source=payload.source,
        device_id=payload.device_id,
        context=payload.context,
        notes=payload.notes,
        correlation_id=uuid.UUID(payload.correlation_id) if payload.correlation_id else None,
        trend="unknown",
        created_by="user",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return GlucoseEventOut(
        id=str(event.id),
        measured_at=event.measured_at,
        value_mg_dl=float(event.value_mg_dl),
        trend=event.trend,
        source=event.source,
        context=event.context,
        hypo_flag=bool(event.hypo_flag) if event.hypo_flag is not None else payload.value_mg_dl < 70,
        hyper_flag=bool(event.hyper_flag) if event.hyper_flag is not None else payload.value_mg_dl > 180,
        notes=event.notes,
    )


@app.post("/api/nutrition/meals", response_model=MealOut, status_code=201)
async def create_meal(
    payload: MealCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    meal = Meal(
        user_id=current_user.id,
        name=payload.name,
        meal_type=payload.meal_type,
        eaten_at=payload.eaten_at,
        total_carbs_g=payload.total_carbs_g,
        total_protein_g=payload.total_protein_g,
        total_fat_g=payload.total_fat_g,
        estimated=payload.estimated,
        notes=payload.notes,
    )
    db.add(meal)
    await db.flush()  # garante meal.id antes dos filhos

    items_out = []
    for item in (payload.items or []):
        mi = MealItem(
            meal_id=meal.id,
            name=item.name,
            carbs_g=item.carbs_g,
            protein_g=item.protein_g,
            fat_g=item.fat_g,
            portion=item.portion,
        )
        db.add(mi)
        await db.flush()
        items_out.append(
            MealItemOut(
                id=str(mi.id),
                name=mi.name,
                carbs_g=float(mi.carbs_g) if mi.carbs_g else None,
                protein_g=float(mi.protein_g) if mi.protein_g else None,
                fat_g=float(mi.fat_g) if mi.fat_g else None,
                portion=mi.portion,
            )
        )

    # Validar e linkar eventos de glicemia
    for link in (payload.linked_glucose_events or []):
        res = await db.execute(
            select(GlucoseEvent.id).where(
                and_(
                    GlucoseEvent.id == uuid.UUID(link.glucose_event_id),
                    GlucoseEvent.user_id == current_user.id,
                )
            )
        )
        if not res.scalar():
            raise HTTPException(
                status_code=400,
                detail=f"Glucose event {link.glucose_event_id} not found."
            )
        db.add(
            MealGlucoseLink(
                meal_id=meal.id,
                glucose_event_id=uuid.UUID(link.glucose_event_id),
                relation=link.relation
            )
        )
    
    await db.commit()
    await db.refresh(meal)
    
    return MealOut(
        id=str(meal.id),
        user_id=str(meal.user_id),
        name=meal.name,
        meal_type=meal.meal_type,
        eaten_at=meal.eaten_at,
        total_carbs_g=float(meal.total_carbs_g) if meal.total_carbs_g else None,
        total_protein_g=float(meal.total_protein_g) if meal.total_protein_g else None,
        total_fat_g=float(meal.total_fat_g) if meal.total_fat_g else None,
        estimated=meal.estimated,
        notes=meal.notes,
        items=items_out,
    )


@app.get("/api/logs", response_model=GlucoseLogsResponse)
async def get_logs(
    time_range: Literal["6h", "24h", "7d", "30d"] = Query("6h", alias="range"),
    source: Literal["manual", "cgm", "all"] = Query("all"),
    granularity: Literal["point", "hour", "day"] = Query("point"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start = get_start_time(time_range)

    query = select(GlucoseEvent).where(
        and_(
            GlucoseEvent.user_id == current_user.id,
            GlucoseEvent.measured_at >= start,
        )
    ).order_by(GlucoseEvent.measured_at.asc())

    if source != "all":
        query = query.where(GlucoseEvent.source == source)

    result = await db.execute(query)
    events = result.scalars().all()

    events_dicts = [
        {
            "value_mg_dl": float(e.value_mg_dl),
            "source":      e.source,
        }
        for e in events
    ]

    tir = compute_time_in_range(events_dicts)

    values = [float(e.value_mg_dl) for e in events] if events else []

    return GlucoseLogsResponse(
        range=time_range,
        granularity=granularity,
        glucose_events=[
            GlucoseEventOut(
                id=str(e.id),
                measured_at=e.measured_at,
                value_mg_dl=float(e.value_mg_dl),
                trend=e.trend,
                source=e.source,
                context=e.context,
                hypo_flag=bool(e.hypo_flag),
                hyper_flag=bool(e.hyper_flag),
                notes=e.notes,
            )
            for e in events
        ],
        metrics=GlucoseMetrics(
            count_events=len(events),
            avg_mg_dl=round(stat_mean(values), 1) if values else None,
            min_mg_dl=min(values) if values else None,
            max_mg_dl=max(values) if values else None,
            time_in_range=TimeInRangeMetrics(**tir),
            distribution=DistributionMetrics(
                manual_count=sum(1 for e in events if e.source == "manual"),
                cgm_count=sum(1 for e in events if e.source == "cgm"),
            ),
        ),
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
