from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.experiment_service import ExperimentService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/experiments", tags=["Biohacking & Experimentação (M11)"])
experiment_service = ExperimentService()

class ExperimentCreate(BaseModel):
    title: str
    hypothesis: str
    metric_to_monitor: str

@router.post("/create")
def create_experiment(data: ExperimentCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    exp = experiment_service.create_experiment(db, current_user, data.dict())
    return {"message": "Experimento iniciado!", "id": exp.id}

@router.get("/list")
def list_experiments(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    exps = experiment_service.list_experiments(db, current_user)
    return exps

@router.post("/close/{experiment_id}")
def close_experiment(experiment_id: int, summary: str, db: Session = Depends(get_db)):
    exp = experiment_service.close_experiment(db, experiment_id, summary)
    if not exp:
        raise HTTPException(404, "Experimento não encontrado")
    return {"message": "Experimento concluído", "results": summary}
