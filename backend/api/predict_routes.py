from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.predict_service import PredictionService

router = APIRouter(prefix="/predict", tags=["Análise Preditiva e Correlações"])

predict_service = PredictionService()

class PredictionResponse(BaseModel):
    analysis: str
    metrics: Optional[dict] = None
    picos: Optional[list] = None

@router.get("/user", response_model=PredictionResponse)
def get_predictive_analysis(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Retorna a análise preditiva dos hábitos do usuário, sugerindo correlações com o perfil glicêmico da rotina.
    """
    result = predict_service.analyze_patterns(current_user, db)
    if "error" in result:
        return {"analysis": result["error"]}
    
    return {"analysis": result["analysis"]}
