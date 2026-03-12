from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.workout_service import WorkoutService
from backend.services.autonomous_service import AutonomousService
from backend.models.user import User, WorkoutProgram, Exercise, WorkoutLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/workouts", tags=["Treino de Alta Performance"])
workout_service = WorkoutService()
autonomous_service = AutonomousService()

class WorkoutLogCreate(BaseModel):
    exercise_id: int
    carga: float
    reps_reais: int
    rpe: int
    feeling: Optional[str] = None
    period: Optional[str] = None
    duration: Optional[int] = None
    completed: Optional[bool] = True
    progression: Optional[bool] = False
    registrado_em: Optional[datetime] = None

class WorkoutLogResponse(BaseModel):
    id: int
    exercise_id: int
    carga: float
    reps_reais: int
    rpe: int
    feeling: Optional[str]
    registrado_em: datetime
    exercise_nome: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/active")
def get_active_workout(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    program = workout_service.get_active_program(db, current_user)
    if not program:
        return {"message": "Nenhum programa ativo."}
    
    exercises = workout_service.get_program_exercises(db, program.id)
    return {
        "program_name": program.nome,
        "exercises": [
            {
                "id": ex.id,
                "nome": ex.nome,
                "series": ex.series,
                "repeticoes": ex.repeticoes,
                "descanso": ex.descanso,
                "notas": ex.notas
            } for ex in exercises
        ]
    }

@router.post("/log")
async def log_workout_session(log: WorkoutLogCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    new_log = WorkoutLog(
        user_id=current_user,
        exercise_id=log.exercise_id,
        carga=log.carga,
        reps_reais=log.reps_reais,
        rpe=log.rpe,
        feeling=log.feeling,
        period=log.period,
        duration=log.duration,
        completed=log.completed,
        progression=log.progression
    )
    db.add(new_log)
    db.commit()
    
    # Gerar tip do coach
    exercise = db.query(Exercise).filter(Exercise.id == log.exercise_id).first()
    tip = await workout_service.generate_elite_tips(exercise.nome, f"Carga: {log.carga}kg, Reps: {log.reps_reais}, RPE: {log.rpe}")
    
    # TRIGGER MOTOR AUTÔNOMO (Módulo 10)
    await autonomous_service.run_proactive_analysis(db, current_user)
    
    return {"message": "Série registrada!", "coach_tip": tip}

@router.get("/performance/{exercise_id}")
async def get_performance(exercise_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    analysis = await workout_service.analyze_performance(db, current_user, exercise_id)
    return analysis

@router.get("/options")
async def get_training_options(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user).first()
    if not user: raise HTTPException(404, "User not found")
    return await workout_service.get_customized_options(user)

@router.get("/patterns")
async def get_workout_patterns(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await workout_service.analyze_performance_patterns(db, current_user)

@router.get("/logs", response_model=List[WorkoutLogResponse])
async def get_workout_logs(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    logs = db.query(WorkoutLog).filter(WorkoutLog.user_id == current_user).order_by(WorkoutLog.registrado_em.desc()).all()
    
    # Adicionar nome do exercício aos logs para facilitar no mobile
    res = []
    for l in logs:
        ex_nome = db.query(Exercise.nome).filter(Exercise.id == l.exercise_id).scalar()
        item = WorkoutLogResponse.from_orm(l)
        item.exercise_nome = ex_nome
        res.append(item)
    return res
