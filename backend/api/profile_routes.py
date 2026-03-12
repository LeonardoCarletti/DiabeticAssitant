from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import io
import json
import pdfplumber
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings
from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.models.user import User, DailyLog

router = APIRouter(prefix="/profile", tags=["Perfil e Rotina Diaria"])

class UserCreate(BaseModel):
    name: str
    email: str
    idade: int
    peso: float
    tipo_diabetes: int
    insulina_basal: str
    insulina_rapida: str
    objetivo: Optional[str] = "Manutencao"
    calorias_alvo: Optional[float] = 2000.0
    proteina_alvo: Optional[float] = 150.0
    carbo_alvo: Optional[float] = 200.0
    gordura_alvo: Optional[float] = 60.0
    nivel_atividade: Optional[str] = "Moderado"
    training_style: Optional[str] = "Hipertrofia"
    injuries: Optional[str] = "Nenhuma"
    equipment: Optional[str] = "Academia Completa"
    caloric_range_limit: Optional[float] = 0.1

class UserResponse(UserCreate):
    id: str
    criado_em: datetime

    class Config:
        from_attributes = True

class DailyLogCreate(BaseModel):
    glicemia: float
    momento: str
    carboidratos: Optional[float] = None
    dose_insulina: Optional[float] = None
    dose_basal: Optional[float] = None
    notas: Optional[str] = None
    registrado_em: Optional[datetime] = None

class DailyLogResponse(BaseModel):
    id: int
    user_id: str
    glicemia: Optional[float]
    momento: str
    carboidratos: Optional[float]
    dose_insulina: Optional[float]
    dose_basal: Optional[float]
    notas: Optional[str]
    registrado_em: datetime

    class Config:
        from_attributes = True

@router.post("/me", response_model=UserResponse)
def sync_user(user: UserCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_user = db.query(User).filter(User.id == current_user).first()
    if db_user:
        for var, value in user.model_dump().items():
            setattr(db_user, var, value) if value else None
    else:
        new_user = User(id=current_user, **user.model_dump())
        db.add(new_user)
        db_user = new_user
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="Perfil nao encontrado. Por favor, complete o onboarding.")
    return user

@router.post("/logs", response_model=DailyLogResponse)
def create_daily_log(log: DailyLogCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    log_data = log.model_dump(exclude_unset=True)
    log_data["user_id"] = current_user
    if log.registrado_em is None:
        log_data["registrado_em"] = datetime.now()
    new_log = DailyLog(**log_data)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

@router.get("/logs", response_model=List[DailyLogResponse])
def get_my_logs(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    logs = db.query(DailyLog).filter(DailyLog.user_id == current_user).order_by(DailyLog.registrado_em.desc()).all()
    return logs

@router.post("/import-universal")
async def import_universal_logs(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_user = db.query(User).filter(User.id == current_user).first()
    if not db_user:
        db_user = User(
            id=current_user,
            name="Usuario",
            email="user@exemplo.com",
            tipo_diabetes=1,
            insulina_basal="Lantus",
            insulina_rapida="Novorapid"
        )
        db.add(db_user)
        db.commit()

    try:
        ext = file.filename.split('.')[-1].lower()
        contents = await file.read()
        extracted_text = ""

        if ext == 'pdf':
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + " "
        elif ext in ['csv', 'txt', 'json']:
            extracted_text = contents.decode('utf-8')
        elif ext in ['xlsx', 'xls']:
            raise HTTPException(400, "Excel nao suportado. Use PDF, CSV, TXT ou JSON.")
        else:
            raise HTTPException(400, "Formato de arquivo nao suportado. Use PDF, CSV, TXT ou JSON.")

        if not extracted_text.strip():
            raise HTTPException(400, "O arquivo parece estar vazio ou nao foi possivel ler o texto.")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.0,
            google_api_key=settings.GEMINI_API_KEY
        )

        system_msg = (
            "Voce e um extrator de dados medicos experiente em relatorios de diabetes. "
            "Converta os dados em um JSON array. "
            "Estrutura: [{\"glicemia\": float|null, \"momento\": string, \"carboidratos\": float|null, "
            "\"dose_insulina\": float|null, \"dose_basal\": float|null, \"notas\": string, "
            "\"registrado_em\": \"YYYY-MM-DDTHH:MM:SS\"}]. "
            "NUNCA use 0 para glicemia ausente, use null. "
            "Retorne APENAS o JSON puro, sem markdown."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("user", "Extraia os dados deste texto:\n\n{texto}")
        ])

        chain = prompt | llm

        if len(extracted_text) > 40000:
            extracted_text = extracted_text[:40000]

        res = chain.invoke({"texto": extracted_text})
        raw_json = res.content.strip()

        if raw_json.startswith('```json'):
            raw_json = raw_json.replace('```json', '').replace('```', '')
        if raw_json.startswith('```'):
            raw_json = raw_json.replace('```', '')

        try:
            logs_array = json.loads(raw_json)
        except json.JSONDecodeError:
            raise HTTPException(500, f"Falha na IA. Saida crua: {raw_json[:200]}")

        logs_adicionados = 0
        for item in logs_array:
            try:
                parsed_dt = datetime.fromisoformat(item.get("registrado_em")) if item.get("registrado_em") else datetime.now()
                glic = item.get("glicemia")
                ins = item.get("dose_insulina")
                bas = item.get("dose_basal")
                if not any([
                    glic and glic > 0,
                    ins and ins > 0,
                    bas and bas > 0,
                    item.get("carboidratos") and item.get("carboidratos") > 0
                ]):
                    continue
                new_db_log = DailyLog(
                    user_id=current_user,
                    glicemia=item.get("glicemia"),
                    momento=item.get("momento", "Importado LLM"),
                    carboidratos=item.get("carboidratos"),
                    dose_insulina=item.get("dose_insulina"),
                    dose_basal=item.get("dose_basal"),
                    notas=item.get("notas"),
                    registrado_em=parsed_dt
                )
                db.add(new_db_log)
                logs_adicionados += 1
            except Exception:
                continue

        db.commit()
        return {"message": f"IA do Gemini importou {logs_adicionados} registros com sucesso!"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
