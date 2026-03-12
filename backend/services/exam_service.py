import io
import json
import logging
import pdfplumber
from typing import List, Dict, Optional
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings
from backend.models.user import MedicalExam, ExamIndicator
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ExamService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0.0,
            google_api_key=settings.GEMINI_API_KEY
        )

    async def process_exam_file(self, db: Session, user_id: str, file_content: bytes, filename: str) -> Dict:
        """
        Extrai texto do arquivo (PDF ou Imagem) e usa Gemini para estruturar os indicadores médicos.
        """
        extracted_text = ""
        
        # 1. Extração de texto (Simplificada para PDF no momento)
        if filename.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                    for page in pdf.pages:
                        extracted_text += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"Erro ao ler PDF: {e}")
                raise Exception("Falha ao processar o arquivo PDF.")
        else:
            # Para imagens, o Gemini Vision poderia processar diretamente o bytes, 
            # mas vamos converter para texto via OCR básico ou enviar o buffer se o modelo suportar.
            # No MVP, vamos avisar que aceitamos PDF ou texto.
            extracted_text = file_content.decode('utf-8', errors='ignore')

        if not extracted_text.strip():
            raise Exception("Não foi possível extrair texto do laudo.")

        # 2. IA Gemini para estruturar os dados
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um especialista em análise de laudos laboratoriais. "
                       "Sua tarefa é extrair os indicadores médicos de um texto bruto e formatar em um JSON estruturado.\n\n"
                       "Estrutura do JSON:\n"
                       "{{\n"
                       "  \"data_exame\": \"YYYY-MM-DD\",\n"
                       "  \"laboratorio\": \"Nome do Lab\",\n"
                       "  \"indicadores\": [\n"
                       "    {{\"nome\": \"Hba1c\", \"valor\": float, \"unidade\": \"%\", \"referencia\": \"4.0 - 5.6\", \"status\": \"Normal\"}},\n"
                       "    {{\"nome\": \"Glicemia de Jejum\", \"valor\": float, \"unidade\": \"mg/dL\", \"referencia\": \"70 - 99\", \"status\": \"Normal\"}}\n"
                       "  ]\n"
                       "}}\n\n"
                       "REGRAS:\n"
                       "1. Extraia o máximo de indicadores possível (Glicose, Hemoglobina Glicada, Colesteróis, Vitaminas, etc).\n"
                       "2. Se o status não estiver explícito (ex: Normal, Alto, Alterado), deduza pela faixa de referência.\n"
                       "3. Retorne APENAS o JSON puro."),
            ("user", "Texto do Laudo:\n\n{texto}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"texto": extracted_text})
        
        # Limpar markdown do JSON se houver
        raw_json = response.content.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json.replace("```json", "").replace("```", "")
        
        try:
            exam_data = json.loads(raw_json)
        except Exception as e:
            logger.error(f"Erro ao parsear JSON do Gemini: {e}\nRaw: {raw_json}")
            raise Exception("A IA falhou ao estruturar os dados do exame.")

        # 3. Salvar no Banco de Dados
        try:
            # Criar o Exame
            data_str = exam_data.get("data_exame")
            data_obj = datetime.strptime(data_str, "%Y-%m-%d") if data_str else datetime.now()
            
            new_exam = MedicalExam(
                user_id=user_id,
                data_exame=data_obj,
                laboratorio=exam_data.get("laboratorio"),
                laudo_bruto=extracted_text[:5000] # Limite para não explodir o DB
            )
            db.add(new_exam)
            db.flush() # Para pegar o id do exame

            # Criar os Indicadores
            added_count = 0
            for ind in exam_data.get("indicadores", []):
                new_indicator = ExamIndicator(
                    exam_id=new_exam.id,
                    nome=ind.get("nome"),
                    valor=ind.get("valor"),
                    unidade=ind.get("unidade"),
                    referencia=ind.get("referencia"),
                    status=ind.get("status")
                )
                db.add(new_indicator)
                added_count += 1
            
            db.commit()
            return {
                "message": "Exame processado e salvo com sucesso!",
                "data": data_obj.strftime("%d/%m/%Y"),
                "indicators_count": added_count
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar no DB: {e}")
            raise Exception(f"Erro ao registrar os dados no banco: {str(e)}")

    def get_evolution_data(self, db: Session, user_id: str, indicator_name: str) -> List[Dict]:
        """
        Retorna a evolução de um indicador específico ao longo do tempo.
        """
        results = db.query(ExamIndicator, MedicalExam.data_exame)\
            .join(MedicalExam)\
            .filter(MedicalExam.user_id == user_id)\
            .filter(ExamIndicator.nome.ilike(f"%{indicator_name}%"))\
            .order_by(MedicalExam.data_exame.asc())\
            .all()
            
        return [
            {
                "data": ind.MedicalExam.data_exame.isoformat(),
                "valor": ind.ExamIndicator.valor,
                "unidade": ind.ExamIndicator.unidade
            } for ind in results
        ]
