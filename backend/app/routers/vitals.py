# backend/app/routers/vitals.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.dependencies import get_current_user, get_supabase_client, AuthUser

router = APIRouter(prefix="/api/vitals", tags=["vitals"])

class VitalRecord(BaseModel):
    metric_type: str  # weight, heart_rate, hrv, blood_pressure, spo2, temperature
    value: float
    unit: Optional[str] = None
    systolic: Optional[float] = None  # for blood_pressure
    diastolic: Optional[float] = None
    notes: Optional[str] = None
    recorded_at: Optional[str] = None

class RecoveryLog(BaseModel):
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None  # 1-5
    hrv: Optional[float] = None
    readiness_score: Optional[int] = None  # 1-10
    fatigue_level: Optional[int] = None  # 1-10
    notes: Optional[str] = None
    date: Optional[str] = None

@router.post("/record")
async def record_vital(
    body: VitalRecord,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        data = {
            "user_id": current_user.id,
            "metric_type": body.metric_type,
            "value": body.value,
            "unit": body.unit,
            "systolic": body.systolic,
            "diastolic": body.diastolic,
            "notes": body.notes,
            "recorded_at": body.recorded_at or datetime.utcnow().isoformat(),
        }
        res = db.table("vital_records").insert(data).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(500, f"Erro: {e}")

@router.get("/history")
async def get_vitals_history(
    metric_type: Optional[str] = None,
    limit: int = 30,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        q = db.table("vital_records").select("*").eq("user_id", current_user.id)
        if metric_type:
            q = q.eq("metric_type", metric_type)
        res = q.order("recorded_at", desc=True).limit(limit).execute()
        return {"records": res.data}
    except Exception as e:
        return {"records": [], "error": str(e)}

@router.get("/latest")
async def get_latest_vitals(
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        metrics = ["weight", "heart_rate", "hrv", "blood_pressure", "spo2"]
        result = {}
        for m in metrics:
            res = db.table("vital_records").select("*").eq("user_id", current_user.id).eq("metric_type", m).order("recorded_at", desc=True).limit(1).execute()
            if res.data:
                result[m] = res.data[0]
        return {"latest": result}
    except Exception as e:
        return {"latest": {}}

@router.post("/recovery")
async def log_recovery(
    body: RecoveryLog,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        data = {
            "user_id": current_user.id,
            "sleep_hours": body.sleep_hours,
            "sleep_quality": body.sleep_quality,
            "hrv": body.hrv,
            "readiness_score": body.readiness_score,
            "fatigue_level": body.fatigue_level,
            "notes": body.notes,
            "date": body.date or datetime.utcnow().date().isoformat(),
        }
        res = db.table("recovery_logs").insert(data).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(500, f"Erro: {e}")

@router.get("/recovery/history")
async def get_recovery_history(
    limit: int = 14,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        res = db.table("recovery_logs").select("*").eq("user_id", current_user.id).order("date", desc=True).limit(limit).execute()
        return {"records": res.data}
    except Exception as e:
        return {"records": []}
