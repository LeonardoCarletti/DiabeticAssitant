from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io
import json
import pdfplumber
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import settings

from backend.core.database import get_db
from backend.core.auth.firebase_auth import get_current_user
from backend.models.user import User, DailyLog

router = APIRouter(prefix="/profile", tags=["Perfil e Rotina Diária"])

# Schemas para Input/Output
class UserCreate(BaseModel):
    name: str
    email: str
    idade: int
    peso: float
    tipo_diabetes: int
    insulina_basal: str
    insulina_rapida: str
    objetivo: Optional[str] = "Manutenção"
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
    # user_id removido do input pois virá do token
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

# Rotas
@router.post("/me", response_model=UserResponse)
def sync_user(user: UserCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Sincroniza os dados do Firebase com o perfil local.
    """
    db_user = db.query(User).filter(User.id == current_user).first()
    if db_user:
        # Update existing
        for var, value in user.model_dump().items():
            setattr(db_user, var, value) if value else None
    else:
        # Create new with Firebase UID
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
        raise HTTPException(status_code=404, detail="Perfil não encontrado. Por favor, complete o onboarding.")
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
    # Garantir existência do usuário
    db_user = db.query(User).filter(User.id == current_user).first()
    if not db_user:
        db_user = User(
            id=current_user, 
            name="Leonardo", 
            email="leonardo@exemplo.com", # Adicionado email default
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
        
        # 1. Extração de Texto baseada no tipo de arquivo
        if ext == 'pdf':
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: extracted_text += text + "\n"
        elif ext in ['csv', 'txt']:
            extracted_text = contents.decode('utf-8')
        elif ext in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(contents))
            extracted_text = df.to_string()
        elif ext == 'json':
            extracted_text = contents.decode('utf-8')
        else:
            raise HTTPException(400, "Formato de arquivo não suportado para importação inteligente. Use PDF, CSV, Excel, TXT ou JSON.")

        if not extracted_text.strip():
            raise HTTPException(400, "O arquivo anexado parece estar vazio ou não foi possível ler o texto.")

        # 2. IA do Gemini faz o Parsing e Normalização
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=settings.GEMINI_API_KEY
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um extrator de dados médicos infalível e experiente em relatórios de diabetes. "
                       "Eu vou te passar um texto bruto copiado de um relatório (MySugr, Freestyle Libre, exames). "
                       "Sua tarefa é converter as linhas de dados em um JSON array.\n\n"
                       "Estrutura do JSON desejada:\n"
                       "[{{\"glicemia\": float ou null, \"momento\": string, \"carboidratos\": float ou null, \"dose_insulina\": float ou null, "
                       "\"dose_basal\": float ou null, \"notas\": string, \"registrado_em\": \"YYYY-MM-DDTHH:MM:SS\"}}]\n\n"
                       "REGRAS CRÍTICAS:\n"
                       "1. NUNCA use 0 para glicemia se o dado estiver ausente. Use null.\n"
                       "2. Extraia apenas os números. Se ler '120 mg/dL', extraia 120. Se ler '5 UI', extraia 5.\n"
                       "3. Interprete datas brasileiras (DD/MM/AAAA) ou americanas conforme o contexto do texto.\n"
                       "4. Se o ano não aparecer, use 2026.\n"
                       "5. O campo 'momento' deve resumir o contexto (ex: 'Café', 'Almoço', 'Dormir').\n"
                       "6. IGNORE COMPLETAMENTE linhas que não possuam nem glicemia nem qualquer dose de insulina.\n"
                       "7. Retorne APENAS o JSON puro, sem markdown."),
            ("user", "Extraia os dados deste texto bruto:\n\n{texto}")
        ])
        
        chain = prompt | llm
        
        # Limitamos o tamanho do texto evitamos estourar o limite de token para planilhas brutas gigantescas no MVP
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
        except json.JSONDecodeError as de:
            raise HTTPException(500, f"Falha na IA ao formatar saída. Saída crua: {raw_json[:200]}")
            
        logs_adicionados = 0
        for item in logs_array:
            try:
                # O item de dicionário vira modelo Pydantic para validação
                # Registrando diretamente por SQLAlchemy pra garantir os nulos
                parsed_dt = datetime.fromisoformat(item.get("registrado_em")) if item.get("registrado_em") else datetime.now()
                
                # Se não tem glicemia nem nenhuma insulina útil (valor > 0), ignoramos
                glic = item.get("glicemia")
                ins = item.get("dose_insulina")
                bas = item.get("dose_basal")
                
                # Se tudo for zero ou null, a linha é lixo de cabeçalho do PDF
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
            except Exception as e:
                continue

        db.commit()
        return {"message": f"I.A. do Gemini processou o arquivo e importou {logs_adicionados} registros com sucesso!"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-csv")
async def import_csv_logs(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')), sep=None, engine='python') # Tenta adivinhar o separador
        
        # Mapeamento Básico de Colunas (pode evoluir para mapeamento inteligente com LLM depois)
        # mySugr envia: Date, Time, Blood Sugar, Carbs, Bolus, Basal
        
        col_maps = {
            'glicemia': ['Blood Sugar', 'Glicemia', 'Glucose', 'BG'],
            'data': ['Date', 'Data'],
            'hora': ['Time', 'Hora'],
            'carbos': ['Carbs', 'Carboidratos'],
            'insulina': ['Bolus', 'Meal Insulin', 'Insulina Rápida'],
            'basal': ['Basal', 'Insulina Basal'],
            'notas': ['Notes', 'Notas', 'Tags']
        }
        
        def find_col(possible_names):
            for col in df.columns:
                if any(p.lower() in str(col).lower() for p in possible_names):
                    return col
            return None
            
        glicemia_col = find_col(col_maps['glicemia'])
        data_col = find_col(col_maps['data'])
        hora_col = find_col(col_maps['hora'])
        
        if not glicemia_col:
            raise HTTPException(400, "Não foi possível identificar a coluna de Glicemia no CSV.")
            
        carbo_col = find_col(col_maps['carbos'])
        ins_col = find_col(col_maps['insulina'])
        basal_col = find_col(col_maps['basal'])
        nota_col = find_col(col_maps['notas'])

        logs_adicionados = 0
        for _, row in df.iterrows():
            try:
                glic = float(row[glicemia_col]) if pd.notna(row[glicemia_col]) else None
                if glic is None: continue # Pula linhas sem glicemia
                
                # Montar Data/Hora
                dt_obj = datetime.now()
                if data_col and pd.notna(row[data_col]):
                    data_str = str(row[data_col])
                    if hora_col and pd.notna(row[hora_col]):
                        data_str += f" {row[hora_col]}"
                    try:
                        dt_obj = pd.to_datetime(data_str).to_pydatetime()
                    except:
                        pass # ignora erro de parse de data
                
                carbo = float(row[carbo_col]) if carbo_col and pd.notna(row[carbo_col]) else None
                ins = float(row[ins_col]) if ins_col and pd.notna(row[ins_col]) else None
                bas = float(row[basal_col]) if basal_col and pd.notna(row[basal_col]) else None
                notas = str(row[nota_col]) if nota_col and pd.notna(row[nota_col]) else None
                
                new_log = DailyLog(
                    user_id=current_user,
                    glicemia=glic,
                    momento="Importado (CSV)",
                    carboidratos=carbo,
                    dose_insulina=ins,
                    dose_basal=bas,
                    notas=notas,
                    registrado_em=dt_obj
                )
                db.add(new_log)
                logs_adicionados += 1
            except Exception as e:
                continue # Pula linhas corrompidas
                
        db.commit()
        return {"message": f"{logs_adicionados} registros importados com sucesso!"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
