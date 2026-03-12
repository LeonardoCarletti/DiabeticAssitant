from sqlalchemy.orm import Session
from backend.models.user import RecoveryLog, User
from datetime import datetime, timedelta

class RecoveryService:
    def calculate_readiness(self, sleep_hours: float, deep_sleep_hours: float, hrv: int, stress_level: int) -> int:
        """
        Calcula o readiness score (0-100) baseado em métricas de elite.
        """
        # Meta: 8h de sono
        sleep_score = min((sleep_hours / 8.0) * 40, 40)
        
        # Meta: 1.5h de sono profundo
        deep_score = min((deep_sleep_hours / 1.5) * 20, 20) if deep_sleep_hours else 0
        
        # Meta Elite: HRV de 60-80 ms
        hrv_score = min((hrv / 70.0) * 40, 40) if hrv else 0
        
        # Penalidade por estresse (1-10)
        stress_penalty = stress_level * 5 if stress_level else 0
        
        score = int(sleep_score + deep_score + hrv_score - stress_penalty)
        return max(0, min(100, score))

    def get_coach_advice(self, score: int) -> str:
        if score >= 85:
            return "🟢 Readiness Máxima! Hoje é o dia para quebrar recordes. Treino de alta intensidade (HIT ou RPE 9-10) liberado."
        elif score >= 70:
            return "🟡 Boa recuperação. Treino de hipertrofia padrão. Mantenha o volume alto, mas monitore a fadiga."
        elif score >= 50:
            return "🟠 Recuperação moderada. Considere um treino de técnica ou diminua a carga em 10-15%. Priorize carbos complexos hoje."
        else:
            return "🔴 Alerta de Fadiga/Overreaching. O sistema recomenda um dia de descanso total ou apenas aeróbico leve/yoga. Priorize o sono hoje."

    def log_recovery(self, db: Session, user_id: str, data: dict):
        score = self.calculate_readiness(
            data.get("sleep_hours", 0),
            data.get("deep_sleep_hours", 0),
            data.get("hrv", 0),
            data.get("stress_level", 5)
        )
        
        new_log = RecoveryLog(
            user_id=user_id,
            sleep_hours=data.get("sleep_hours"),
            deep_sleep_hours=data.get("deep_sleep_hours"),
            hrv=data.get("hrv"),
            resting_heart_rate=data.get("resting_heart_rate"),
            stress_level=data.get("stress_level"),
            readiness_score=score,
            notas=data.get("notas")
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log, self.get_coach_advice(score)

    def get_latest_recovery(self, db: Session, user_id: str):
        return db.query(RecoveryLog).filter(RecoveryLog.user_id == user_id).order_by(RecoveryLog.registrado_em.desc()).first()
