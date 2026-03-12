import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.models.user import User, WorkoutProgram, Exercise, WorkoutLog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings

logger = logging.getLogger(__name__)

class WorkoutService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
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
            # Tenta limpar markdown do json se vier
            clean_res = response.content.strip().replace('```json', '').replace('```', '')
            return json.loads(clean_res)
        except:
            return [{"title": "Plano A", "description": "Treino Padrão de Elite"}, {"title": "Plano B", "description": "Foco em Progressão"}]

    def get_active_program(self, db: Session, user_id: str) -> Optional[WorkoutProgram]:
        return db.query(WorkoutProgram).filter(WorkoutProgram.user_id == user_id, WorkoutProgram.ativo == True).first()

    def get_program_exercises(self, db: Session, program_id: int) -> List[Exercise]:
        return db.query(Exercise).filter(Exercise.program_id == program_id).order_by(Exercise.ordem).all()

    async def analyze_performance(self, db: Session, user_id: str, exercise_id: int) -> Dict:
        """
        Analisa a progressão de carga e volume para um exercício específico.
        """
        logs = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id, WorkoutLog.exercise_id == exercise_id)\
                 .order_by(WorkoutLog.registrado_em.desc()).limit(5).all()
        
        if not logs:
            return {"status": "no_data", "message": "Ainda não há registros para este exercício."}

        # Exemplo simples de análise: se a carga subiu
        performance_data = []
        for log in reversed(logs):
            performance_data.append({
                "data": log.registrado_em.strftime("%d/%m"),
                "carga": log.carga,
                "volume": log.carga * log.reps_reais
            })
            
        return {
            "status": "success",
            "history": performance_data,
            "current_max": max([l.carga for l in logs])
        }

    async def analyze_performance_patterns(self, db: Session, user_id: str) -> str:
        """
        Analisa padrões entre como o usuário se sente, a carga e a progressão.
        """
        logs = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id)\
                 .order_by(WorkoutLog.registrado_em.desc()).limit(20).all()
        
        if not logs:
            return "Sem dados de treino suficientes para padrões."

        summary = []
        for l in logs:
            summary.append(f"Data: {l.registrado_em.date()}, Feeling: {l.feeling}, Carga: {l.carga}, Progrediu: {l.progression}")

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Analista de Performance. Identifique padrões entre o humor/feeling do atleta e a progressão de carga."),
            ("user", "Logs do Atleta:\n{logs}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"logs": "\n".join(summary)})
        return response.content

    async def generate_elite_tips(self, exercise_name: str, performance_summary: str) -> str:
        """
        Gera dicas de execução de elite baseadas em Hany Rambod e Pacholok.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Treinador de Bodybuilding de Elite. Suas referências são Hany Rambod (FST-7) e Fabricio Pacholok. "
                       "Dê uma dica motivacional e técnica 'brutal' para o próximo treino do atleta."),
            ("user", "Exercício: {exercicio}\nResumo da Performance Atual: {performance}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "exercicio": exercise_name,
            "performance": performance_summary
        })
        
        return response.content
