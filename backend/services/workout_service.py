import logging
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.user import (
    User, TrainingProtocol, TrainingSession, 
    Exercise, ExerciseSet, WorkoutLog, TrainingFeedback
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings

logger = logging.getLogger(__name__)

class WorkoutService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.2,
            google_api_key=settings.GEMINI_API_KEY
        )

    async def get_customized_options(self, user: User) -> List[Dict]:
        """
        Gera 3 opções de sessões de treino baseadas no estilo e equipamentos do usuário.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Coach de Bodybuilding Elite. O usuário busca um estilo {estilo}. "
                       "Considere lesões: {lesoes} e Equipamentos: {equipos}. "
                       "Proponha 3 opções de focos de treino para hoje (ex: Costas/Bíceps, Foco em Força, Recuperação Ativa)."),
            ("user", "Sugira 3 caminhos de treino curto e direto em JSON format: [{\"title\": \"\", \"description\": \"\"}]")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "estilo": user.training_style or "Hipertrofia",
            "lesoes": user.injuries or "Nenhuma",
            "equipos": user.equipment or "Academia Completa"
        })
        
        try:
            clean_res = response.content.strip().replace('```json', '').replace('```', '')
            return json.loads(clean_res)
        except:
            return [{"title": "Plano A", "description": "Treino Padrão de Elite"}, {"title": "Plano B", "description": "Foco em Progressão"}]

    def get_active_protocol(self, db: Session, user_id: str) -> Optional[TrainingProtocol]:
        return db.query(TrainingProtocol).filter(
            TrainingProtocol.user_id == user_id, 
            TrainingProtocol.is_active == True
        ).first()

    def get_protocol_sessions(self, db: Session, protocol_id: int) -> List[TrainingSession]:
        return db.query(TrainingSession).filter(
            TrainingSession.protocol_id == protocol_id
        ).order_by(TrainingSession.order).all()

    def get_session_details(self, db: Session, session_id: int) -> Optional[TrainingSession]:
        return db.query(TrainingSession).filter(TrainingSession.id == session_id).first()

    async def log_set_execution(self, db: Session, user_id: str, set_data: Dict) -> WorkoutLog:
        """
        Registra a execução de uma série específica dentro de um exercício.
        """
        new_log = WorkoutLog(
            user_id=user_id,
            exercise_id=set_data.get("exercise_id"),
            set_id=set_data.get("set_id"),
            weight=set_data.get("weight"),
            reps=set_data.get("reps"),
            rpe=set_data.get("rpe"),
            feeling=set_data.get("feeling"),
            notes=set_data.get("notes")
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log

    async def analyze_progress(self, db: Session, user_id: str, exercise_id: int) -> Dict:
        """
        Analisa a progressão de carga e volume para um exercício específico ao longo do tempo.
        """
        logs = db.query(WorkoutLog).filter(
            WorkoutLog.user_id == user_id, 
            WorkoutLog.exercise_id == exercise_id
        ).order_by(desc(WorkoutLog.timestamp)).limit(10).all()
        
        if not logs:
            return {"status": "no_data", "message": "Sem dados suficientes para análise."}

        # Agrupar por data para ver a evolução das sessões
        history = []
        for log in reversed(logs):
            history.append({
                "date": log.timestamp.strftime("%Y-%m-%d"),
                "weight": log.weight,
                "reps": log.reps,
                "volume": log.weight * log.reps
            })
            
        # Cálculo de tendência
        first_vol = history[0]["volume"]
        last_vol = history[-1]["volume"]
        growth = ((last_vol - first_vol) / first_vol * 100) if first_vol > 0 else 0

        return {
            "history": history,
            "total_growth_pct": round(growth, 2),
            "status": "improving" if growth > 5 else "stagnated" if growth > -5 else "dropping"
        }

    async def generate_elite_tips(self, exercise_name: str, performance_summary: str) -> str:
        """
        Gera dicas de execução de elite.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Treinador de Bodybuilding de Elite. Suas referências são Hany Rambod (FST-7) e Fabricio Pacholok. "
                       "Dê uma dica técnica e motivacional brutal para o atleta."),
            ("user", "Exercício: {exercicio}\nResumo da Performance Atual: {performance}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "exercicio": exercise_name,
            "performance": performance_summary
        })
        
        return response.content

    def add_coach_feedback(self, db: Session, coach_id: str, user_id: str, content: str, feedback_type: str = "daily") -> TrainingFeedback:
        feedback = TrainingFeedback(
            user_id=user_id,
            coach_id=coach_id,
            content=content,
            feedback_type=feedback_type
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
