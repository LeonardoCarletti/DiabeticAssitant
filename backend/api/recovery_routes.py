from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.recovery_service import RecoveryService
from backend.services.autonomous_service import AutonomousService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/recovery", tags=["Motor de Recuperação (M8)"])
recovery_service = RecoveryService()
autonomous_service = AutonomousService()

class RecoveryCreate(BaseModel):
    sleep_hours: float
    deep_sleep_hours: Optional[float] = None
    hrv: Optional[int] = None
    resting_heart_rate: Optional[int] = None
    stress_level: Optional[int] = 5
    notas: Optional[str] = None

@router.post("/log")
async def log_recovery(data: RecoveryCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    log, advice = recovery_service.log_recovery(db, current_user, data.dict())
    
    # TRIGGER MOTOR AUTÔNOMO (Módulo 10) para recalcular prontidão cruzada
    await autonomous_service.run_proactive_analysis(db, current_user)
    
    return {
        "message": "Dados de recuperação salvos!",
        "readiness_score": log.readiness_score,
        "coach_advice": advice
    }

@router.get("/latest")
def get_latest_recovery(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    log = recovery_service.get_latest_recovery(db, current_user)
    if not log:
        return {"message": "Sem logs de recuperação."}
    
    advice = recovery_service.get_coach_advice(log.readiness_score)
    return {
        "sleep_hours": log.sleep_hours,
        "hrv": log.hrv,
        "readiness_score": log.readiness_score,
        "advice": advice,
        "registrado_em": log.registrado_em.isoformat()
    }
