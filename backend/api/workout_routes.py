from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.workout_service import WorkoutService
from backend.services.ai_trainer_service import AITrainerService
from backend.models.user import (
    User, TrainingProtocol, TrainingSession, 
    Exercise, ExerciseSet, WorkoutLog, TrainingFeedback
)
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/workouts", tags=["Treino Elite - Módulo Avançado"])
workout_service = WorkoutService()
ai_trainer_service = AITrainerService()

# --- SCHEMAS ---

class SetLogCreate(BaseModel):
    exercise_id: int
    set_id: int
    weight: float
    reps: int
    rpe: Optional[int] = None
    feeling: Optional[str] = None
    notes: Optional[str] = None

class AIWorkoutRequest(BaseModel):
    request: str

class AIChatMessage(BaseModel):
    role: str
    content: str

class AIChatRequest(BaseModel):
    messages: List[AIChatMessage]

# --- ROUTES ---

@router.get("/active-protocol")
def get_active_protocol(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    protocol = workout_service.get_active_protocol(db, current_user)
    if not protocol:
        return {"message": "Sem protocolo ativo."}
    
    sessions = workout_service.get_protocol_sessions(db, protocol.id)
    return {
        "id": protocol.id,
        "name": protocol.name,
        "sessions": [
            {
                "id": s.id,
                "name": s.name,
                "order": s.order,
                "day_of_week": s.day_of_week
            } for s in sessions
        ]
    }

@router.get("/session/{session_id}")
def get_session_details(session_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    session = workout_service.get_session_details(db, session_id)
    if not session:
        raise HTTPException(404, "Sessão não encontrada")
    
    return {
        "name": session.name,
        "warmup": session.warmup_notes,
        "mobility": session.mobility_notes,
        "cardio": session.cardio_notes,
        "exercises": [
            {
                "id": ex.id,
                "name": ex.name,
                "stimulus": ex.stimulus_type,
                "photo": ex.photo_url,
                "notes": ex.notes,
                "sets": [
                    {
                        "id": s.id,
                        "number": s.set_number,
                        "type": s.set_type,
                        "planned_reps": s.planned_reps,
                        "planned_weight": s.planned_weight
                    } for s in ex.sets
                ]
            } for ex in session.exercises
        ]
    }

@router.post("/log-set")
async def log_set(log_data: SetLogCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    log = await workout_service.log_set_execution(db, current_user, log_data.dict())
    
    # Gerar tip rápida baseada na carga
    ex_name = db.query(Exercise.name).filter(Exercise.id == log_data.exercise_id).scalar()
    tip = await workout_service.generate_elite_tips(ex_name, f"Carga: {log.weight}kg, Reps: {log.reps}")
    
    return {"message": "Série salva!", "coach_tip": tip}

@router.get("/analysis/{exercise_id}")
async def get_exercise_analysis(exercise_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await workout_service.analyze_progress(db, current_user, exercise_id)

# --- AI TRAINER ROUTES ---

@router.post("/ai/prescribe")
async def ai_prescribe_workout(req: AIWorkoutRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user).first()
    plan = await ai_trainer_service.generate_workout_plan(user, req.request)
    return plan

@router.post("/ai/chat")
async def ai_chat(req: AIChatRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user).first()
    response = await ai_trainer_service.chat_interaction(user, [m.dict() for m in req.messages])
    return {"response": response}
