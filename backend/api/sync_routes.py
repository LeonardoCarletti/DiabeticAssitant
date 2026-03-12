from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.models.user import RecoveryLog, DailyLog, NutritionLog, User
from backend.services.recovery_service import RecoveryService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/sync", tags=["Health Sync Hub"])
recovery_service = RecoveryService()

class HealthSyncPack(BaseModel):
    steps: Optional[int] = None
    active_calories: Optional[float] = None
    heart_rate_avg: Optional[int] = None
    hrv: Optional[int] = None
    sleep_hours: Optional[float] = None
    deep_sleep_hours: Optional[float] = None
    resting_heart_rate: Optional[int] = None
    recorded_at: Optional[datetime] = None

@router.post("/health")
async def sync_health_data(pack: HealthSyncPack, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Sincroniza dados de wearables com os logs internos.
    """
    recorded_at = pack.recorded_at or datetime.utcnow()
    
    # 1. Se houver dados de sono ou HRV, criamos um RecoveryLog
    if pack.sleep_hours is not None or pack.hrv is not None:
        recovery_data = {
            "sleep_hours": pack.sleep_hours,
            "deep_sleep_hours": pack.deep_sleep_hours,
            "hrv": pack.hrv,
            "resting_heart_rate": pack.resting_heart_rate,
            "stress_level": 5, # Valor padrão se não vier
            "notas": f"Sync automático via Health Hub em {recorded_at.isoformat()}"
        }
        # Filtrar None
        recovery_data = {k: v for k, v in recovery_data.items() if v is not None}
        
        recovery_log, advice = recovery_service.log_recovery(db, current_user, recovery_data)
        
    # 2. Podemos adicionar lógica futura para passos/calorias em DailyLog se desejado
    # Por enquanto focamos no cérebro do coach: Recuperação e HRV.

    return {
        "status": "success",
        "synced_at": datetime.utcnow().isoformat(),
        "readiness_updated": True if (pack.sleep_hours or pack.hrv) else False
    }

@router.get("/status")
def get_sync_status(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    last_recovery = db.query(RecoveryLog).filter(RecoveryLog.user_id == current_user).order_by(RecoveryLog.registrado_em.desc()).first()
    return {
        "last_sync": last_recovery.registrado_em.isoformat() if last_recovery else None,
        "source": "Health Hub"
    }
