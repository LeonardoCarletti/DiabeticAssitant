from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from backend.core.database import get_db
from backend.services.autonomous_service import AutonomousService
from pydantic import BaseModel

router = APIRouter(prefix="/autonomous", tags=["Motor Autônomo"])
autonomous_service = AutonomousService()

class InsightResponse(BaseModel):
    id: int
    topic: str
    message: str
    severity: str
    read: bool
    registrado_em: str

@router.get("/insights/{user_id}")
async def get_insights(user_id: str, db: Session = Depends(get_db)):
    insights = autonomous_service.get_unread_insights(db, user_id)
    return [
        {
            "id": i.id,
            "topic": i.topic,
            "message": i.message,
            "severity": i.severity,
            "read": i.read,
            "registrado_em": i.registrado_em.isoformat()
        } for i in insights
    ]

@router.post("/insights/read/{insight_id}")
def mark_read(insight_id: int, db: Session = Depends(get_db)):
    success = autonomous_service.mark_as_read(db, insight_id)
    if not success:
        raise HTTPException(404, "Insight not found")
    return {"message": "Marcado como lido"}

@router.post("/trigger/{user_id}")
async def manual_trigger(user_id: str, db: Session = Depends(get_db)):
    """
    Trigger manual para forçar a análise autônoma (útil para testes).
    """
    insight = await autonomous_service.run_proactive_analysis(db, user_id)
    return {"message": "Análise concluída", "new_insight": insight.topic if insight else None}

@router.post("/morning-prep/{user_id}")
async def trigger_morning(user_id: str, db: Session = Depends(get_db)):
    insight = await autonomous_service.run_morning_prep(db, user_id)
    return {"message": "Morning Prep gerado", "insight": insight.message}

@router.post("/night-review/{user_id}")
async def trigger_night(user_id: str, db: Session = Depends(get_db)):
    insight = await autonomous_service.run_night_review(db, user_id)
    return {"message": "Night Review gerado", "insight": insight.message}
