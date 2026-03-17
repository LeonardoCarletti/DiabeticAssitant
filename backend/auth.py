# ============================================================
# BLOCO 6A.2 — Auth real com JWT Supabase
# Arquivo: backend/auth.py
# ============================================================

import os
from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

SUPABASE_URL             = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Supabase assina os JWTs com o JWT_SECRET do projeto.
# Ele pode ser obtido em: Supabase Dashboard → Settings → API → JWT Secret
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()

@dataclass
class AuthenticatedUser:
    id: str           # UUID do usuário (sub do JWT)
    email: Optional[str]
    phone: Optional[str]
    role: str         # "authenticated" para usuários reais

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """
    Valida o Bearer JWT emitido pelo Supabase Auth.
    Lança 401 se o token for inválido, expirado ou de outro projeto.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[SUPABASE_JWT_ALGORITHM],
            options={"verify_aud": False},  # Supabase não usa audience padrão
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificador de usuário (sub).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload.get("role", "")
    if role != "authenticated":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Token não pertence a um usuário autenticado.",
        )

    return AuthenticatedUser(
        id=user_id,
        email=payload.get("email"),
        phone=payload.get("phone"),
        role=role,
    )
