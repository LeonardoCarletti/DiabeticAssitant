from sqlalchemy.orm import Session
from backend.models.user import Experiment
from datetime import datetime

class ExperimentService:
    def create_experiment(self, db: Session, user_id: str, data: dict):
        new_exp = Experiment(
            user_id=user_id,
            title=data.get("title"),
            hypothesis=data.get("hypothesis"),
            metric_to_monitor=data.get("metric_to_monitor")
        )
        db.add(new_exp)
        db.commit()
        db.refresh(new_exp)
        return new_exp

    def list_experiments(self, db: Session, user_id: str):
        return db.query(Experiment).filter(Experiment.user_id == user_id).all()

    def close_experiment(self, db: Session, experiment_id: int, summary: str):
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if exp:
            exp.status = "concluído"
            exp.end_date = datetime.utcnow()
            exp.results_summary = summary
            db.commit()
            return exp
        return None
