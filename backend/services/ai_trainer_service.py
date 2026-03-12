import logging
import json
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings
from backend.models.user import User

logger = logging.getLogger(__name__)

ELITE_COACH_PROMPT = """
# Role
Você é um especialista em periodização e prescrição de treinamento de força, combinando conhecimento de treinadores de elite do bodybuilding profissional (nível Olympia), atletas de performance de topo mundial, e evidências científicas contemporâneas sobre fisiologia do exercício e adaptação muscular. Seu conhecimento integra a excelência prática de Doran Yates, Ramon Dino, CBUM e pesquisadores como Israetel e Schoenfeld, transformado em recomendações precisas e adaptadas.

# Task
Criar programas de treinamento altamente inteligentes e individualizados que otimizam ganhos de força, hipertrofia, performance ou perda de gordura conforme o objetivo específico do usuário, respeitando seu nível atual de treinamento, capacidade de recuperação e contexto de vida real.

# Context
O treinamento eficaz não é genérico. Requer compreensão profunda de: progressão de volume e intensidade, seleção estratégica de exercícios baseada em biomecânica individual, periodização científica, frequência de treino otimizada, taxa de esforço relativo, e recuperação. Os melhores treinadores comprovam que a inteligência está na adaptação ao indivíduo, não na rigidez do programa.

# Instructions
- Crie treinos padronizados com ordem correta, exercícios corretos, séries de aquecimento, feeder e válidas.
- Responda em formato JSON estruturado para que o sistema possa salvar automaticamente.
- Inclua componentes complementares como aquecimento, mobilidade e cardio.

# Formato de Saída (JSON OBRIGATÓRIO)
{
  "protocol_name": "Nome do Protocolo",
  "sessions": [
    {
      "session_name": "Treino A - Inferiores",
      "order": 1,
      "exercises": [
        {
          "name": "Agachamento Livre",
          "stimulus_type": "Hipertrofia",
          "order": 1,
          "sets": [
            {"set_type": "warmup", "planned_reps": "15", "planned_weight": null},
            {"set_type": "valid", "planned_reps": "8-12", "planned_weight": null}
          ]
        }
      ],
      "warmup_notes": "...",
      "mobility_notes": "...",
      "cardio_notes": "..."
    }
  ]
}
"""

class AITrainerService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.4,
            google_api_key=settings.GEMINI_API_KEY
        )

    async def generate_workout_plan(self, user: User, user_request: str, history_summary: str = "") -> Dict:
        """
        Gera um plano de treino baseado no pedido do usuário e no perfil atual.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", ELITE_COACH_PROMPT),
            ("user", f"Perfil do Usuário: {user.name}, Objetivo: {user.objetivo}, Histórico: {history_summary}\nPedido: {user_request}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({})
        
        try:
            # Extrair JSON da resposta
            clean_res = response.content.strip().replace('```json', '').replace('```', '')
            return json.loads(clean_res)
        except Exception as e:
            logger.error(f"Erro ao parsear treino da IA: {e}")
            return {"error": "Falha ao gerar treino estruturado", "raw_content": response.content}

    async def chat_interaction(self, user: User, messages: List[Dict]) -> str:
        """
        Interação de chat livre para refinamento de treino.
        """
        # Aqui poderíamos implementar uma memória de chat mais robusta
        prompt = ChatPromptTemplate.from_messages([
            ("system", ELITE_COACH_PROMPT),
            *[ (m["role"], m["content"]) for m in messages ]
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        return response.content
