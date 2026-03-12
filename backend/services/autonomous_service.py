from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.user import User, DailyLog, NutritionLog, WorkoutLog, Insight, RecoveryLog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings
from datetime import datetime, timedelta


from backend.services.rag_service import RAGService

class AutonomousService:
    def __init__(self, rag_service: RAGService = None):
        self.rag_service = rag_service
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3, # Um pouco de criatividade para sugestões proativas
            google_api_key=settings.GEMINI_API_KEY
        )

    async def run_proactive_analysis(self, db: Session, user_id: str):
        """
        Executa uma análise cross-module para detectar padrões e riscos.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user: return

        # Buscar dados recentes (últimas 48h para proatividade rápida)
        since = datetime.utcnow() - timedelta(hours=48)
        
        glicemia_logs = db.query(DailyLog).filter(DailyLog.user_id == user_id, DailyLog.registrado_em >= since).all()
        nutrition_logs = db.query(NutritionLog).filter(NutritionLog.user_id == user_id, NutritionLog.registrado_em >= since).all()
        workout_logs = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id, WorkoutLog.registrado_em >= since).all()
        recovery_logs = db.query(RecoveryLog).filter(RecoveryLog.user_id == user_id, RecoveryLog.registrado_em >= since).all()

        if not glicemia_logs and not nutrition_logs and not workout_logs and not recovery_logs:
            return

        # Preparar dados para o LLM
        data_summary = {
            "glicemia": [{"valor": l.glicemia, "momento": l.momento, "hora": l.registrado_em.isoformat()} for l in glicemia_logs],
            "dieta": [{"alimento": l.alimento, "cal": l.calorias, "prot": l.proteina, "carb": l.carbo, "fat": l.gordura, "tipo": l.meal_type} for l in nutrition_logs],
            "treino": [{"carga": l.carga, "reps": l.reps_reais, "feeling": l.feeling, "progrediu": l.progression} for l in workout_logs],
            "recuperacao": [{"sono": l.sleep_hours, "hrv": l.hrv, "readiness": l.readiness_score} for l in recovery_logs]
        }

        # 3. Buscar contexto científico (RAG) se disponível
        scientific_context = ""
        if self.rag_service:
            try:
                # Criar uma query baseada nos logs de glicemia ou tendência
                query = topic if 'topic' in locals() else "Type 1 Diabetes performance optimization"
                if glicemia_logs:
                    last_gl = glicemia_logs[0].glicemia
                    if last_gl > 180: query = "hyperglycemia exercise management"
                    elif last_gl < 70: query = "hypoglycemia recovery elite athlete"
                
                rag_res = self.rag_service.ask(query)
                scientific_context = rag_res.get("answer", "")
            except:
                pass

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Motor Autônomo 'Leo Coach'. Sua função é ser PROATIVO. "
                       "Analise os dados de glicemia, dieta, treino e RECUPERAÇÃO e use o contexto científico fornecido. "
                       "Identifique um insight crítico ou sugestão técnica valiosa. "
                       "Considere a prontidão (Readiness) para sugerir deload ou intensidade máxima. "
                       "Seja direto, técnico e use um tom de coach de alto nível."),
            ("user", "Contexto Científico (RAG):\n{context}\n\n"
                    "Dados do Atleta (48h):\n{data}\n\n"
                    "Gere um Insight curto no formato:\nTópico: [Treino/Dieta/Metabólico]\nMensagem: [Sua análise e sugestão baseada em ciência]\nSeveridade: [info/warning/critical]")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "data": str(data_summary),
            "context": scientific_context or "Nenhum contexto extra disponível."
        })
        
        # Parsear resposta (Simples por enquanto)
        content = response.content
        lines = content.split('\n')
        topic, message, severity = "Geral", content, "info"
        
        for line in lines:
            if "Tópico:" in line: topic = line.replace("Tópico:", "").strip()
            if "Mensagem:" in line: message = line.replace("Mensagem:", "").strip()
            if "Severidade:" in line: severity = line.replace("Severidade:", "").strip().lower()
            
        # Limpezas extras (remover tags markdown se houver)
        topic = topic.replace("**", "").replace("#", "")
        severity = severity.replace("severidade:", "").strip()

        # Salvar Insight no Banco
        new_insight = Insight(
            user_id=user_id,
            topic=topic,
            message=message,
            severity=severity
        )
        db.add(new_insight)
        db.commit()
        db.refresh(new_insight)
        return new_insight

    async def run_morning_prep(self, db: Session, user_id: str):
        """
        Gera o cockpit matinal do atleta.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user: return

        # Pegar última recuperação
        last_rec = db.query(RecoveryLog).filter(RecoveryLog.user_id == user_id).order_by(RecoveryLog.registrado_em.desc()).first()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Coach José Leonardo. Início de dia. "
                       "Analise o sono e HRV do atleta. Proponha o foco do dia: "
                       "Intensity (se readiness > 80), Focus (se 60-80), ou Recovery (se < 60). "
                       "Sugira também a meta calórica ideal para este estado."),
            ("user", "Dados Matinais:\n- Atleta: {name}\n- Sono: {sleep}h\n- HRV: {hrv}\n- Prontidão: {readiness}\n"
                    "Gere um Insight de Tópico 'Morning Prep' com Severidade 'info'.")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "name": user.name,
            "sleep": last_rec.sleep_hours if last_rec else "N/A",
            "hrv": last_rec.hrv if last_rec else "N/A",
            "readiness": last_rec.readiness_score if last_rec else "N/A"
        })
        
        return await self._parse_and_save(db, user_id, response.content)

    async def run_night_review(self, db: Session, user_id: str):
        """
        Gera a revisão noturna e plano para amanhã.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user: return

        # Resumo do dia (Nutrição e Treino)
        today = datetime.utcnow().date()
        daily_nut = db.query(NutritionLog).filter(NutritionLog.user_id == user_id, func.date(NutritionLog.registrado_em) == today).all()
        daily_work = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id, func.date(WorkoutLog.registrado_em) == today).all()
        
        total_cal = sum([n.calorias for n in daily_nut])
        work_done = len(daily_work) > 0

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Coach José Leonardo. Fim de dia. "
                       "Analise se o atleta cumpriu as metas. Seja 'papai' se ele treinou pesado e bateu macros, "
                       "ou seja 'brutal' se ele falhou. Sugira o ajuste para amanhã."),
            ("user", "Resumo do Dia:\n- Calorias Totais: {cal}\n- Treinou: {work}\n- Objetivo Atleta: {obj}\n"
                    "Gere um Insight de Tópico 'Night Review' com Severidade 'info'.")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "cal": total_cal,
            "work": "Sim" if work_done else "Não",
            "obj": user.objetivo
        })
        
        return await self._parse_and_save(db, user_id, response.content)

    async def _parse_and_save(self, db: Session, user_id: str, content: str):
        lines = content.split('\n')
        topic, message, severity = "Geral", content, "info"
        for line in lines:
            if "Tópico:" in line: topic = line.replace("Tópico:", "").strip()
            elif "Mensagem:" in line: message = line.replace("Mensagem:", "").strip()
            elif "Severidade:" in line: severity = line.replace("Severidade:", "").strip().lower()

        new_insight = Insight(
            user_id=user_id,
            topic=topic.replace("**", "").replace("#", ""),
            message=message,
            severity=severity.replace("severidade:", "").strip()
        )
        db.add(new_insight)
        db.commit()
        db.refresh(new_insight)
        return new_insight

    def get_unread_insights(self, db: Session, user_id: str):
        return db.query(Insight).filter(Insight.user_id == user_id, Insight.read == False).order_by(Insight.registrado_em.desc()).all()

    def mark_as_read(self, db: Session, insight_id: int):
        insight = db.query(Insight).filter(Insight.id == insight_id).first()
        if insight:
            insight.read = True
            db.commit()
            return True
        return False
