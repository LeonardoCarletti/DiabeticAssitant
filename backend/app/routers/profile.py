# backend/app/routers/profile.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.dependencies import get_supabase_client, get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    diabetes_type: Optional[str] = None  # type1 | type2 | gestational | other
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    insulin_user: Optional[bool] = None
    target_glucose_min: Optional[float] = None
    target_glucose_max: Optional[float] = None
    hba1c_target: Optional[float] = None
    timezone: Optional[str] = None
    data_processing_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None

@router.get("/")
async def get_profile(
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    result = (
        db.table("user_profiles")
        .select("*")
        .eq("id", str(user.id))
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Perfil não encontrado")
    return result.data

@router.patch("/")
async def update_profile(
    payload: ProfileUpdate,
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    data = {k: str(v) if isinstance(v, date) else v
            for k, v in payload.dict().items() if v is not None}
    if not data:
        raise HTTPException(400, "Nenhum campo para atualizar")
    result = (
        db.table("user_profiles")
        .update(data)
        .eq("id", str(user.id))
        .execute()
    )
    return result.data[0] if result.data else {"status": "updated"}
