import logging
import statistics
from collections import defaultdict
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

        values = [l.glicemia for l in logs if l.glicemia]

        if not values:
            return {"tir": 0, "std": 0, "count": 0}

        # Time in Range (TIR)
        tir_count = len([v for v in values if 70 <= v <= 180])
        tir_percent = (tir_count / len(values)) * 100

        # Variabilidade
        std_val = statistics.stdev(values) if len(values) > 1 else 0

        return {
            "tir": round(tir_percent, 1),
            "std": round(std_val, 1),
            "count": len(values)
        }

    def detect_patterns(self, db: Session, user_id: str) -> List[Dict]:
        """
        Identifica horários críticos de picos glicêmicos.
        """
        logs = db.query(DailyLog).filter(DailyLog.user_id == user_id).all()
        if not logs:
            return []

        data = [{"glicemia": l.glicemia, "hora": l.registrado_em.hour} for l in logs if l.glicemia]

        if not data:
            return []

        # Agrupar por hora e calcular média de glicemia
        hourly_sums = defaultdict(list)
        for entry in data:
            hourly_sums[entry["hora"]].append(entry["glicemia"])

        picos = []
        for hora, vals in sorted(hourly_sums.items()):
            avg = sum(vals) / len(vals)
            if avg > 180:
                picos.append({"hora": hora, "glicemia": round(avg, 1)})

        return picos
