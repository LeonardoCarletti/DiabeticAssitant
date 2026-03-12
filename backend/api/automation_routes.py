from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.cgm_service import CGMService
from backend.services.autonomous_service import AutonomousService
from backend.services.nutrition_service import NutritionService
from backend.services.workout_service import WorkoutService
from backend.models.user import NutritionLog, WorkoutLog, DailyLog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/automation", tags=["Automação e Integrações (M9)"])
cgm_service = CGMService()
autonomous_service = AutonomousService()
nutrition_service = NutritionService()
workout_service = WorkoutService()

class CGMData(BaseModel):
    value: int
    timestamp: str

class VoiceCommand(BaseModel):
    command: str

@router.post("/cgm/ingest")
async def ingest_cgm(data: List[CGMData], db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    stream = [{"value": d.value, "timestamp": d.timestamp} for d in data]
    count = cgm_service.process_cgm_stream(db, current_user, stream)
    
    # Trigger AI analysis after batch ingest
    if count > 0:
        await autonomous_service.run_proactive_analysis(db, current_user)
        
    return {"message": "Dados do sensor processados", "count": count}

@router.post("/voice-log")
async def voice_log(cmd: VoiceCommand, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Usa I.A. para converter um comando de voz em log estruturado e SALVAR no banco.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um mestre interpretador de logs de saúde para atletas diabéticos. "
                   "Sua saída DEVE ser um JSON puro compatível com os modelos do banco de dados. "
                   "Tipos possíveis: 'nutrition', 'workout', 'insulin'.\n"
                   "Regras:\n"
                   "1. Nutrition: {'type': 'nutrition', 'data': {'alimento', 'calorias', 'carbo', 'proteina', 'gordura', 'meal_type'}}\n"
                   "2. Workout: {'type': 'workout', 'data': {'exercise_id', 'carga', 'reps_reais', 'rpe'}}\n"
                   "3. Insulin: {'type': 'insulin', 'data': {'valor', 'momento'}}\n"
                   "Se o usuário não disser macros, estime baseado no alimento para um atleta de elite."),
        ("user", "{command}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"command": cmd.command})
    
    import json
    try:
        # Limpar markdown se houver
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        
        log_type = result.get("type")
        log_data = result.get("data")
        
        msg = "Log interpretado e salvo!"
        
        if log_type == "nutrition":
            new_log = NutritionLog(user_id=current_user, **log_data)
            db.add(new_log)
        elif log_type == "workout":
            # Aqui precisaríamos do ID do exercício, por agora logamos como texto livre nas notas se não achar ID
            new_log = WorkoutLog(user_id=current_user, **log_data)
            db.add(new_log)
        elif log_type == "insulin":
            new_log = DailyLog(user_id=current_user, glicemia=0, momento=log_data.get("momento", "bolus"), insulin_applied=log_data.get("valor"))
            db.add(new_log)
            
        db.commit()
        
        # Trigger Autonomous Motor
        await autonomous_service.run_proactive_analysis(db, current_user)
        
        return {"status": "success", "message": msg, "data": result}
    except Exception as e:
        return {"status": "error", "message": f"Falha ao processar: {str(e)}", "raw": response.content}
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile

@router.post("/voice-log-file")
async def voice_log_file(file: UploadFile = FastAPIFile(...), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Recebe um arquivo de áudio e usa o Gemini (Multimodal)
    para transcrever e converter em MÚLTIPLOS logs estruturados se necessário.
    """
    try:
        audio_content = await file.read()
        
        from langchain_core.messages import HumanMessage
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY)
        
        # Prompt aprimorado para múltiplos logs
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Você é um mestre interpretador de logs de saúde para atletas diabéticos.\n"
                                          "Interprete o áudio e retorne uma LISTA de JSONs puros.\n"
                                          "O usuário pode falar várias coisas ao mesmo tempo (Glicemia, Insulina, Comida, Treino).\n\n"
                                          "Formatos permitidos na lista:\n"
                                          "1. {'type': 'daily', 'data': {'glicemia', 'momento', 'dose_insulina', 'dose_basal', 'carboidratos', 'notas'}}\n"
                                          "2. {'type': 'nutrition', 'data': {'alimento', 'calorias', 'carbo', 'proteina', 'gordura', 'meal_type'}}\n"
                                          "3. {'type': 'workout', 'data': {'carga', 'reps_reais', 'rpe', 'duration'}}\n\n"
                                          "Exemplo de saída: [{'type': 'daily', 'data': {...}}, {'type': 'nutrition', 'data': {...}}]\n"
                                          "Se o valor não for dito, omita ou use null. Retorne APENAS o array JSON puros."},
                {"type": "media", "mime_type": file.content_type, "data": audio_content},
            ]
        )
        
        response = llm.invoke([message])
        
        import json
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        # Garante que seja uma lista
        logs_to_process = json.loads(clean_json)
        if not isinstance(logs_to_process, list):
            logs_to_process = [logs_to_process]
        
        processed_count = 0
        for item in logs_to_process:
            log_type = item.get("type")
            log_data = item.get("data")
            
            if log_type == "nutrition":
                new_log = NutritionLog(user_id=current_user, **log_data)
                db.add(new_log)
                processed_count += 1
            elif log_type == "workout":
                new_log = WorkoutLog(user_id=current_user, **log_data)
                db.add(new_log)
                processed_count += 1
            elif log_type in ["daily", "insulin"]:
                # 'insulin' mapeia para daily no banco
                new_log = DailyLog(user_id=current_user, **log_data)
                db.add(new_log)
                processed_count += 1
            
        db.commit()
        await autonomous_service.run_proactive_analysis(db, current_user)
        
        return {
            "status": "success", 
            "message": f"{processed_count} logs processados com sucesso!", 
            "data": logs_to_process
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Erro no processamento de áudio: {str(e)}"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Erro no processamento de áudio: {str(e)}"}
