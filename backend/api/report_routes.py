from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.services.report_service import ReportService
import os

router = APIRouter(prefix="/reports", tags=["Relatórios e Exportação (Fase 4)"])
report_service = ReportService()

@router.get("/expert")
async def get_expert_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Gera e retorna o PDF do relatório de performance elite.
    """
    try:
        report_path = report_service.generate_expert_report(db, current_user)
        
        if not os.path.exists(report_path):
            raise HTTPException(status_code=500, detail="Erro ao gerar arquivo PDF.")
            
        # Agendar remoção do arquivo temporário após o envio
        background_tasks.add_task(os.remove, report_path)
        
        return FileResponse(
            path=report_path,
            filename=f"Relatorio_Performance_Leo.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
