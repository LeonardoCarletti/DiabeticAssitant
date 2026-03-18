# backend/app/routers/logs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.dependencies import get_supabase_client, get_current_user

router = APIRouter(prefix="/api/logs", tags=["logs"])

# ── SCHEMAS ──────────────────────────────────────────────────────

class GlucoseEventCreate(BaseModel):
    value_mg_dl: float = Field(..., ge=20, le=600)
    source: str = Field("manual")
    context: Optional[str] = None  # fasting | post_meal | before_sleep | exercise
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None
    device_id: Optional[str] = None

    @validator("source")
    def validate_source(cls, v):
        allowed = {"manual", "cgm", "libre", "dexcom", "apple_health", "google_fit"}
        if v not in allowed:
            raise ValueError(f"source deve ser um de: {allowed}")
        return v

class MealItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    carbs_g: Optional[float] = Field(None, ge=0, le=500)
    protein_g: Optional[float] = Field(None, ge=0, le=300)
    fat_g: Optional[float] = Field(None, ge=0, le=300)
    fiber_g: Optional[float] = Field(None, ge=0, le=100)
    calories_kcal: Optional[float] = Field(None, ge=0, le=5000)
    glycemic_index: Optional[int] = Field(None, ge=0, le=100)
    portion: Optional[str] = None

class MealCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    meal_type: str = Field(...)
    eaten_at: Optional[datetime] = None
    notes: Optional[str] = None
    glucose_before_mg_dl: Optional[float] = Field(None, ge=20, le=600)
    glucose_after_mg_dl: Optional[float] = Field(None, ge=20, le=600)
    insulin_units: Optional[float] = Field(None, ge=0, le=100)
    items: List[MealItemCreate] = []

    @validator("meal_type")
    def validate_meal_type(cls, v):
        allowed = {"breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"}
        if v not in allowed:
            raise ValueError(f"meal_type deve ser um de: {allowed}")
        return v

# ── GLUCOSE ──────────────────────────────────────────────────────

@router.post("/glucose", status_code=201)
async def log_glucose(
    payload: GlucoseEventCreate,
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    data = payload.dict()
    data["user_id"] = str(user.id)
    data["measured_at"] = (data["measured_at"] or datetime.utcnow()).isoformat()
    data["hypo_flag"] = data["value_mg_dl"] < 70
    data["hyper_flag"] = data["value_mg_dl"] > 180
    result = db.table("glucose_events").insert(data).execute()
    if not result.data:
        raise HTTPException(500, "Falha ao salvar leitura de glicose")
    return result.data[0]

@router.get("/glucose")
async def list_glucose(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    result = (
        db.table("glucose_events")
        .select("*")
        .eq("user_id", str(user.id))
        .order("measured_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data

@router.get("/glucose/tir")
async def get_tir(
    days: int = Query(14, ge=1, le=90),
    low: float = Query(70.0),
    high: float = Query(180.0),
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    """TIR seguindo diretrizes ADA 2024. Alvo: ≥70% no range 70-180 mg/dL."""
    result = db.rpc(
        "calculate_tir",
        {"p_user_id": str(user.id), "p_days": days, "p_low": low, "p_high": high},
    ).execute()
    if not result.data:
        return {"total_readings": 0, "tir_percent": None}
    return result.data[0]

@router.get("/glucose/daily-summary")
async def get_daily_summary(
    days: int = Query(30, ge=1, le=90),
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    result = (
        db.table("daily_glucose_summary")
        .select("*")
        .eq("user_id", str(user.id))
        .order("day", desc=True)
        .limit(days)
        .execute()
    )
    return result.data

# ── MEALS ─────────────────────────────────────────────────────────

@router.post("/meals", status_code=201)
async def log_meal(
    payload: MealCreate,
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    meal_data = payload.dict(exclude={"items"})
    meal_data["user_id"] = str(user.id)
    meal_data["eaten_at"] = (meal_data["eaten_at"] or datetime.utcnow()).isoformat()

    meal_result = db.table("meals").insert(meal_data).execute()
    if not meal_result.data:
        raise HTTPException(500, "Falha ao salvar refeição")
    meal_id = meal_result.data[0]["id"]

    if payload.items:
        items_data = [{"meal_id": meal_id, **item.dict()} for item in payload.items]
        db.table("meal_items").insert(items_data).execute()

    summary = (
        db.table("meal_nutrition_summary")
        .select("*")
        .eq("id", meal_id)
        .single()
        .execute()
    )
    return summary.data

@router.get("/meals")
async def list_meals(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    result = (
        db.table("meal_nutrition_summary")
        .select("*")
        .eq("user_id", str(user.id))
        .order("eaten_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data

@router.get("/context")
async def get_ai_context(
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    result = db.rpc("build_ai_context", {"p_user_id": str(user.id)}).execute()
    if not result.data:
        raise HTTPException(500, "Falha ao montar contexto")
    return result.data[0]
