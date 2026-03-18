# backend/app/dependencies.py
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import jwt

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

security = HTTPBearer()

def get_supabase_client() -> Client:
    """Retorna cliente Supabase com service role (acesso total, bypass RLS)."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(500, "Supabase env vars missing")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class AuthUser:
    def __init__(self, user_id: str, email: str):
        self.id = user_id
        self.email = email

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    """Valida JWT do Supabase e retorna o usuário autenticado."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        email = payload.get("email", "")
        if not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
        return AuthUser(user_id=user_id, email=email)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token inválido: {str(e)}")
