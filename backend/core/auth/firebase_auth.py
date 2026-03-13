import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Request, HTTPException, Depends
from backend.core.config import settings
import os
import json

# Inicializar Firebase Admin
# Suporta dois modos:
# 1. FIREBASE_SERVICE_ACCOUNT_JSON: conteudo JSON como string (recomendado para Vercel/producao)
# 2. FIREBASE_SERVICE_ACCOUNT_PATH: caminho para arquivo .json (desenvolvimento local)

if not firebase_admin._apps:
    # Modo 1: JSON como variavel de ambiente (Vercel)
    firebase_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    if firebase_json:
        try:
            service_account_info = json.loads(firebase_json)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            print("Firebase inicializado com sucesso via variavel de ambiente JSON.")
        except Exception as e:
            print(f"ERRO ao inicializar Firebase via JSON env: {e}")
    # Modo 2: Arquivo local (desenvolvimento)
    elif os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase inicializado com sucesso via arquivo local.")
    else:
        print(f"AVISO: Firebase nao configurado. Rodando em modo MOCK (apenas para desenvolvimento).")
        print(f"Para producao: defina FIREBASE_SERVICE_ACCOUNT_JSON como variavel de ambiente na Vercel.")

async def get_current_user(request: Request):
    """
    Middleware para validar o Firebase ID Token vindo no header Authorization.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Se nao houver token, por enquanto permitimos 'leo_prod' para retrocompatibilidade no MVP
        # Mas no app final, isso vai lancar 401.
        return "leo_prod_mock_id"
        # raise HTTPException(status_code=401, detail="Token nao fornecido")

    id_token = auth_header.split(" ")[1]

    # Se Firebase nao foi inicializado (modo mock), retorna ID do token direto
    if not firebase_admin._apps:
        return id_token

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token invalido: {str(e)}")
