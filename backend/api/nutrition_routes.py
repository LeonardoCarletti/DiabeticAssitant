from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.nutrition_service import NutritionService
from backend.services.autonomous_service import AutonomousService
from backend.models.user import User, NutritionLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/nutrition", tags=["Nutrição de Alta Performance"])
nutrition_service = NutritionService()
autonomous_service = AutonomousService()

class MealCreate(BaseModel):
    alimento: str
    calorias: float
    proteina: float
    carbo: float
    gordura: float
    meal_type: Optional[str] = "Outros" # Café, Almoço, etc
    user_feeling: Optional[str] = None
    momento: str # ex: "Pré-treino"
    registrado_em: Optional[datetime] = None

class NutritionLogResponse(BaseModel):
    id: int
    alimento: str
    calorias: float
    proteina: float
    carbo: float
    gordura: float
    meal_type: str
    momento: str
    registrado_em: datetime

    class Config:
        from_attributes = True

@router.post("/log")
async def log_meal(meal: MealCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    # Criar registro de nutrição
    new_log = NutritionLog(
        user_id=current_user,
        alimento=meal.alimento,
        calorias=meal.calorias,
        proteina=meal.proteina,
        carbo=meal.carbo,
        gordura=meal.gordura,
        momento=meal.momento,
        meal_type=meal.meal_type,
        user_feeling=meal.user_feeling
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    # Análise de timing
    user = db.query(User).filter(User.id == current_user).first()
    feedback = await nutrition_service.analyze_meal_timing(user, new_log, 100.0)
    
    # TRIGGER MOTOR AUTÔNOMO (Módulo 10)
    await autonomous_service.run_proactive_analysis(db, current_user)
    
    return {"message": "Refeição registrada!", "feedback_coach": feedback}

@router.get("/status")
async def get_nutrition_status(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    targets = nutrition_service.calculate_macro_targets(user)
    current = nutrition_service.get_daily_status(db, current_user)
    
    # Adicionar Orientação da IA se houver desvios
    guidance = await nutrition_service.get_advice_on_deviations(user, current, targets)
    
    return {
        "targets": targets,
        "current": current,
        "guidance": guidance,
        "remaining": {
            "calorias": targets["calorias"] - current["calorias"],
            "proteina": targets["proteina"] - current["proteina"],
            "carbo": targets["carbo"] - current["carbo"],
            "gordura": targets["gordura"] - current["gordura"]
        }
    }

@router.get("/logs", response_model=List[NutritionLogResponse])
async def get_nutrition_logs(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    logs = db.query(NutritionLog).filter(NutritionLog.user_id == current_user).order_by(NutritionLog.registrado_em.desc()).all()
    return logs
