# backend/app/routers/nutrition.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.dependencies import get_current_user, get_supabase_client, AuthUser

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])

class MealLog(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    description: str
    calories: Optional[int] = None
    carbs_g: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    glucose_before: Optional[float] = None
    glucose_after: Optional[float] = None
    notes: Optional[str] = None
    logged_at: Optional[str] = None

class NutritionGoal(BaseModel):
    calories_target: Optional[int] = None
    carbs_target_g: Optional[float] = None
    protein_target_g: Optional[float] = None
    fat_target_g: Optional[float] = None
    water_target_ml: Optional[int] = 2000

@router.post("/log")
async def log_meal(
    body: MealLog,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        data = {
            "user_id": current_user.id,
            "meal_type": body.meal_type,
            "description": body.description,
            "calories": body.calories,
            "carbs_g": body.carbs_g,
            "protein_g": body.protein_g,
            "fat_g": body.fat_g,
            "fiber_g": body.fiber_g,
            "glucose_before": body.glucose_before,
            "glucose_after": body.glucose_after,
            "notes": body.notes,
            "logged_at": body.logged_at or datetime.utcnow().isoformat(),
        }
        res = db.table("meal_logs").insert(data).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(500, f"Erro: {e}")

@router.get("/today")
async def get_today_meals(
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        today = datetime.utcnow().date().isoformat()
        res = db.table("meal_logs").select("*").eq("user_id", current_user.id).gte("logged_at", today).execute()
        meals = res.data or []
        total_calories = sum(m.get("calories", 0) or 0 for m in meals)
        total_carbs = sum(m.get("carbs_g", 0) or 0 for m in meals)
        total_protein = sum(m.get("protein_g", 0) or 0 for m in meals)
        total_fat = sum(m.get("fat_g", 0) or 0 for m in meals)
        return {
            "meals": meals,
            "totals": {
                "calories": total_calories,
                "carbs_g": total_carbs,
                "protein_g": total_protein,
                "fat_g": total_fat,
            }
        }
    except Exception as e:
        return {"meals": [], "totals": {}}

@router.get("/history")
async def get_nutrition_history(
    limit: int = 30,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        res = db.table("meal_logs").select("*").eq("user_id", current_user.id).order("logged_at", desc=True).limit(limit).execute()
        return {"meals": res.data}
    except Exception as e:
        return {"meals": []}

@router.post("/goals")
async def set_nutrition_goals(
    body: NutritionGoal,
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        data = {
            "user_id": current_user.id,
            "calories_target": body.calories_target,
            "carbs_target_g": body.carbs_target_g,
            "protein_target_g": body.protein_target_g,
            "fat_target_g": body.fat_target_g,
            "water_target_ml": body.water_target_ml,
        }
        res = db.table("nutrition_goals").upsert(data, on_conflict="user_id").execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(500, f"Erro: {e}")

@router.get("/goals")
async def get_nutrition_goals(
    current_user: AuthUser = Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    try:
        res = db.table("nutrition_goals").select("*").eq("user_id", current_user.id).limit(1).execute()
        return {"goals": res.data[0] if res.data else {}}
    except Exception as e:
        return {"goals": {}}
