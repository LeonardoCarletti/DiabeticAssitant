import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Request, HTTPException, Depends
from backend.core.config import settings
import os

# Inicializar Firebase Admin
if not firebase_admin._apps:
    if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
    else:
        # Mock para desenvolvimento se o arquivo não existir
        print(f"AVISO: Arquivo {settings.FIREBASE_SERVICE_ACCOUNT_PATH} não encontrado. Rodando em modo MOCK.")

async def get_current_user(request: Request):
    """
    Middleware para validar o Firebase ID Token vindo no header Authorization.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Se não houver token, por enquanto permitimos 'leo_prod' para retrocompatibilidade no MVP
        # Mas no app final, isso vai lançar 401.
        return "leo_prod_mock_id"
        # raise HTTPException(status_code=401, detail="Token não fornecido")

    id_token = auth_header.split(" ")[1]
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
