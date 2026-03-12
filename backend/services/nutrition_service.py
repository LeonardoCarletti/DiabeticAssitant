import json
import logging
from typing import List, Dict, Optional
from backend.models.user import User, NutritionLog
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0.2,
            google_api_key=settings.GEMINI_API_KEY
        )

    def calculate_macro_targets(self, user: User) -> Dict:
        """
        Calcula as metas de macros baseadas no objetivo do usuário.
        Usa Mifflin-St Jeor como base se não houver alvo manual.
        """
        # Se os alvos já estiverem definidos (não 0), usa eles.
        if user.calorias_alvo and user.calorias_alvo > 0:
            return {
                "calorias": user.calorias_alvo,
                "proteina": user.proteina_alvo,
                "carbo": user.carbo_alvo,
                "gordura": user.gordura_alvo,
                "objetivo": user.objetivo or "Manutenção"
            }
        
        # Cálculo TDEE Básico (Mifflin-St Jeor)
        # BMR = 10*peso + 6.25*altura - 5*idade + 5 (macho)
        # Assumindo altura de 175cm se não houver no banco (precisamos adicionar altura depois)
        bmr = (10 * user.peso) + (6.25 * 175) - (5 * user.idade) + 5
        
        # Fator Atividade
        factors = {"Sedentário": 1.2, "Leve": 1.375, "Moderado": 1.55, "Ativo": 1.725, "Atleta": 1.9}
        tdee = bmr * factors.get(user.nivel_atividade, 1.55)
        
        # Ajuste de Fase
        phase = user.objetivo or "Manutenção"
        if phase == "Bulking":
            tdee += 400
        elif phase == "Cutting":
            tdee -= 400
            
        return {
            "calorias": round(tdee),
            "proteina": round(user.peso * 2.0), # 2g/kg default athlete
            "carbo": round((tdee * 0.45) / 4), # 45% carbo
            "gordura": round((tdee * 0.25) / 9), # 25% gordura
            "objetivo": phase
        }

    async def get_advice_on_deviations(self, user: User, daily_status: Dict, targets: Dict) -> str:
        """
        Gera um alerta inteligente se o usuário estiver fora da faixa calórica permitida.
        """
        cal_diff = daily_status["calorias"] - targets["calorias"]
        limit = targets["calorias"] * user.caloric_range_limit
        
        if abs(cal_diff) <= limit:
            return "Dentro da faixa. Continue focado no plano!"

        state = "EXCESSO" if cal_diff > 0 else "DÉFICIT"
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é o Coach de Nutrição Elite. O usuário está em {state} calórico significativo. "
                       "Dê uma orientação 'brutal' mas inteligente sobre como compensar nos próximos dias ou ajustar a insulina se necessário."),
            ("user", "Dados:\n- Objetivo: {objetivo}\n- Meta: {target}kcal\n- Consumido: {current}kcal\n- Diferença: {diff}kcal")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "state": state,
            "objetivo": targets["objetivo"],
            "target": targets["calorias"],
            "current": daily_status["calorias"],
            "diff": cal_diff
        })
        return response.content

    def get_daily_status(self, db: Session, user_id: str) -> Dict:
        """
        Calcula o quanto o usuário já ingeriu no dia atual.
        """
        from sqlalchemy import func
        from datetime import date
        
        today = date.today()
        summary = db.query(
            func.sum(NutritionLog.calorias),
            func.sum(NutritionLog.proteina),
            func.sum(NutritionLog.carbo),
            func.sum(NutritionLog.gordura)
        ).filter(NutritionLog.user_id == user_id, func.date(NutritionLog.registrado_em) == today).first()

        cal, prot, carb, fat = summary or (0, 0, 0, 0)
        
        # Garantir que não retorne None
        return {
            "calorias": cal or 0,
            "proteina": prot or 0,
            "carbo": carb or 0,
            "gordura": fat or 0
        }

    async def analyze_meal_timing(self, user: User, log_entry: NutritionLog, last_glucose: float) -> str:
        """
        Analisa se o timing do alimento é adequado para o controle glicêmico e performance.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um Nutricionista e Nutrólogo especialista em atletas de elite e diabéticos. "
                       "Analise a refeição do usuário em relação à sua glicemia atual e seus objetivos objetivos de performance.\n"
                       "Considere: Timing de carbo, carga glicêmica, e impacto na recuperação muscular."),
            ("user", "Dados do Usuário:\n"
                     "- Objetivo: {objetivo}\n"
                     "- Glicemia atual: {glicemia} mg/dL\n"
                     "Refeição:\n"
                     "- Alimento: {alimento}\n"
                     "- Macros: {cal}kcal, {prot}g prot, {carb}g carbo, {fat}g gordura\n"
                     "- Momento: {momento}\n\n"
                     "Dê um feedback curto e 'brutal' (estilo coach Pacholok) sobre essa refeição.")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "objetivo": user.objetivo,
            "glicemia": last_glucose,
            "alimento": log_entry.alimento,
            "cal": log_entry.calorias,
            "prot": log_entry.proteina,
            "carb": log_entry.carbo,
            "fat": log_entry.gordura,
            "momento": log_entry.momento
        })
        
        return response.content
