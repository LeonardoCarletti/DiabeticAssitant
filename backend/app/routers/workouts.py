# backend/app/routers/workouts.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.dependencies import get_current_user, get_supabase_client, AuthUser

router = APIRouter(prefix="/api/workouts", tags=["workouts"])

class WorkoutLog(BaseModel):
    workout_type: str  # e.g. "Musculacao", "Corrida", "Natacao"
    duration_min: int
    rpe: Optional[int] = None  # 0-10
    notes: Optional[str] = None
    calories: Optional[int] = None
    date: Optional[str] = None

class WorkoutGenerate(BaseModel):
    level: str = "Intermediario"
    goal: str = "Hipertrofia"
    glucose: Optional[float] = 120.0

@router.get("/history")
async def get_workout_history(
    limit: int = 20,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        res = db.table("workout_logs").select("*").eq("user_id", current_user.id).order("created_at", desc=True).limit(limit).execute()
        return {"workouts": res.data}
    except Exception as e:
        return {"workouts": [], "error": str(e)}

@router.post("/log")
async def log_workout(
    body: WorkoutLog,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        data = {
            "user_id": current_user.id,
            "workout_type": body.workout_type,
            "duration_min": body.duration_min,
            "rpe": body.rpe,
            "notes": body.notes,
            "calories": body.calories,
            "date": body.date or datetime.utcnow().isoformat(),
        }
        res = db.table("workout_logs").insert(data).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(500, f"Erro ao salvar treino: {e}")

@router.get("/stats")
async def get_workout_stats(
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        res = db.table("workout_logs").select("*").eq("user_id", current_user.id).execute()
        workouts = res.data or []
        total = len(workouts)
        total_min = sum(w.get("duration_min", 0) for w in workouts)
        avg_rpe = round(sum(w.get("rpe", 0) or 0 for w in workouts) / total, 1) if total > 0 else 0
        return {"total_workouts": total, "total_minutes": total_min, "avg_rpe": avg_rpe}
    except Exception as e:
        return {"total_workouts": 0, "total_minutes": 0, "avg_rpe": 0}
