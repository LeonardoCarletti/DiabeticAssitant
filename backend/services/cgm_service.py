from sqlalchemy.orm import Session
from backend.models.user import DailyLog
from datetime import datetime, timedelta
import statistics
import math

class CGMService:
    def process_cgm_stream(self, db: Session, user_id: str, stream_data: list):
        """
        Processa um stream de dados de sensor contínuo (CGM).
        Formato esperado: [{"value": 110, "timestamp": "2024-03-09T10:00:00"}, ...]
        """
        logs_created = 0
        for entry in stream_data:
            # Evitar duplicatas por timestamp (Simplificado)
            registrado_em = datetime.fromisoformat(entry["timestamp"])

            # Verificar se já existe log nesse minuto
            exists = db.query(DailyLog).filter(
                DailyLog.user_id == user_id,
                DailyLog.registrado_em == registrado_em
            ).first()

            if not exists:
                new_log = DailyLog(
                    user_id=user_id,
                    glicemia=entry["value"],
                    momento="sensor",
                    registrado_em=registrado_em
                )
                db.add(new_log)
                logs_created += 1

        db.commit()
        return logs_created

    def calculate_cgm_metrics(self, db: Session, user_id: str, hours: int = 24):
        """
        Calcula métricas avançadas de CGM (TIR, GMI, Variabilidade).
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        logs = db.query(DailyLog).filter(DailyLog.user_id == user_id, DailyLog.registrado_em >= since).all()

        if not logs:
            return None

        values = [l.glicemia for l in logs if l.glicemia is not None]

        if not values:
            return None

        avg = statistics.mean(values)
        tir = (len([v for v in values if 70 <= v <= 180]) / len(values)) * 100
        sd = statistics.stdev(values) if len(values) > 1 else 0

        # GMI (Glucose Management Indicator) - Estimativa de HbA1c
        gmi = 3.31 + (0.02392 * avg)

        return {
            "avg": round(avg, 1),
            "tir": round(tir, 1),
            "sd": round(sd, 1),
            "gmi": round(gmi, 2),
            "count": len(values)
        }
