from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.exam_service import ExamService
from backend.models.user import MedicalExam, ExamIndicator

router = APIRouter(prefix="/exams", tags=["Exames Médicos e Laboratoriais"])
exam_service = ExamService()

@router.post("/upload")
async def upload_exam(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint para upload e processamento de exames.
    """
    content = await file.read()
    try:
        result = await exam_service.process_exam_file(db, current_user, content, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
def get_exam_summary(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Retorna um resumo dos últimos indicadores de saúde.
    """
    # Busca os exames do usuário
    exams = db.query(MedicalExam).filter(MedicalExam.user_id == current_user).order_by(MedicalExam.data_exame.desc()).all()
    if not exams:
        return {"message": "Nenhum exame encontrado."}
    
    summary = []
    for exam in exams[:3]: # Últimos 3 exames
        indicators = db.query(ExamIndicator).filter(ExamIndicator.exam_id == exam.id).all()
        summary.append({
            "id": exam.id,
            "data": exam.data_exame.strftime("%d/%m/%Y"),
            "laboratorio": exam.laboratorio,
            "indicadores": [
                {
                    "nome": i.nome,
                    "valor": i.valor,
                    "unidade": i.unidade,
                    "status": i.status
                } for i in indicators
            ]
        })
    return summary

@router.get("/evolution/{indicator_name}")
def get_indicator_evolution(indicator_name: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Retorna os dados históricos de um indicador específico (ex: Hba1c) para gráficos.
    """
    # Busca indicadores que combinam com o nome (ex: para pegar 'Hemoglobina Glicada' via 'hba1c')
    # No MVP, vamos usar o ilike.
    data = db.query(ExamIndicator.valor, MedicalExam.data_exame, ExamIndicator.unidade)\
             .join(MedicalExam)\
             .filter(MedicalExam.user_id == current_user)\
             .filter(ExamIndicator.nome.ilike(f"%{indicator_name}%"))\
             .order_by(MedicalExam.data_exame.asc()).all()
             
    return [{"valor": d[0], "data": d[1].strftime("%Y-%m-%d"), "unidade": d[2]} for d in data]
