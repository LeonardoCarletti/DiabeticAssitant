from sqlalchemy.orm import Session
from backend.models.user import DailyLog, User, RecoveryLog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings
from backend.services.metabolic_service import MetabolicService
import httpx

class PredictionService:
    def __init__(self):
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        import requests
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,
            google_api_key=settings.GEMINI_API_KEY
        )
        self.metabolic_service = MetabolicService()

    def analyze_patterns(self, user_id: str, db: Session):
        """
        Gera uma análise preditiva e de correlações baseada no histórico do usuário usando LLM.
        """
        logs = db.query(DailyLog).filter(DailyLog.user_id == user_id).order_by(DailyLog.registrado_em.asc()).all()
        recovery_logs = db.query(RecoveryLog).filter(RecoveryLog.user_id == user_id).order_by(RecoveryLog.registrado_em.desc()).limit(10).all()
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"error": "Perfil não encontrado. Por favor, preencha seus dados de atleta no Perfil."}

        # Métricas Metabólicas (Módulo 5)
        m_metrics = self.metabolic_service.calculate_metrics(db, user_id)
        m_patterns = self.metabolic_service.detect_patterns(db, user_id)

        if not logs:
            return {"error": "Sem dados registrados."}

        if len(logs) < 15:
            return {"error": f"O Agente Analítico precisa de no mínimo 15 registros para identificar padrões reais. Atualmente você tem {len(logs)} registros."}

        # Converter para texto tabular sem pandas
        data = []
        for log in logs:
            data.append({
                "data": log.registrado_em.strftime("%Y-%m-%d %H:%M"),
                "glicemia": log.glicemia,
                "momento": log.momento,
                "carbos": log.carboidratos,
                "insulina": log.dose_insulina,
                "notas": log.notas
            })

        # Pegar os últimos 30 registros e formatar como tabela
        recent_data = data[-30:]
        header = "data | glicemia | momento | carbos | insulina | notas"
        rows = ["\t|".join(str(v) for v in d.values()) for d in recent_data]
        logs_text = header + "\n" + "\n".join(rows)

        # Dados de Recuperação
        rec_rows = []
        for r in recovery_logs:
            rec_rows.append(
                f"{r.registrado_em.strftime('%Y-%m-%d')} | readiness={r.readiness_score} | hrv={r.hrv} | sono={r.sleep_hours} | stress={r.stress_level}"
            )
        rec_text = "\n".join(rec_rows) if rec_rows else "Nenhum dado de recuperação"

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Analista Preditivo do Leo, especialista em biohacking e performance para atletas com Diabetes."
                       " O paciente com diabetes tipo {tipo} utiliza insulina rápida ({rapida}) e basal ({basal})."
                       " Você deve cruzar dados de Glicemia com Recuperação (Sono/HRV/Stress)."
                       " Lembre-se: Baixo HRV ou pouco sono profundo aumentam a resistência à insulina e o cortisol."
                       " Métricas Metabólicas: TIR: {tir}%, SD: {std}mg/dL."),
            ("user", "### Histórico Glicêmico (últimos 30 logs):\n{logs_data}\n\n"
                     "### Histórico de Recuperação (últimos 10 registros):\n{rec_data}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "tipo": user.tipo_diabetes,
            "rapida": user.insulina_rapida,
            "basal": user.insulina_basal,
            "tir": m_metrics["tir"],
            "std": m_metrics["std"],
            "logs_data": logs_text,
            "rec_data": rec_text
        })

        return {
            "analysis": response.content,
            "metrics": m_metrics,
            "picos": m_patterns
        }
