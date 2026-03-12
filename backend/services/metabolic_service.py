import logging
import pandas as pd
from sqlalchemy.orm import Session
from backend.models.user import DailyLog
from typing import Dict, List

logger = logging.getLogger(__name__)

class MetabolicService:
    def calculate_metrics(self, db: Session, user_id: str) -> Dict:
        """
        Calcula as métricas de tempo em faixa (TIR) e variabilidade glicêmica.
        Faixa recomendada: 70 a 180 mg/dL.
        """
        logs = db.query(DailyLog).filter(DailyLog.user_id == user_id).all()
        if not logs:
            return {"tir": 0, "std": 0, "count": 0}

        df = pd.DataFrame([{"glicemia": l.glicemia} for l in logs if l.glicemia])
        if df.empty:
            return {"tir": 0, "std": 0, "count": 0}

        # Time in Range (TIR)
        tir_count = len(df[(df['glicemia'] >= 70) & (df['glicemia'] <= 180)])
        tir_percent = (tir_count / len(df)) * 100

        # Variabilidade
        std_val = df['glicemia'].std()
        
        return {
            "tir": round(tir_percent, 1),
            "std": round(std_val, 1) if not pd.isna(std_val) else 0,
            "count": len(df)
        }

    def detect_patterns(self, db: Session, user_id: str) -> List[Dict]:
        """
        Identifica horários críticos de picos glicêmicos.
        """
        logs = db.query(DailyLog).filter(DailyLog.user_id == user_id).all()
        if not logs:
            return []

        df = pd.DataFrame([{"glicemia": l.glicemia, "hora": l.registrado_em.hour} for l in logs if l.glicemia])
        if df.empty:
            return []

        # Agrupar por hora e ver média de glicemia
        hourly_avg = df.groupby('hora')['glicemia'].mean().reset_index()
        picos = hourly_avg[hourly_avg['glicemia'] > 180].to_dict('records')
        
        return picos
