from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

class MockUser:
    def __init__(self, id: str):
        self.id = id

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> MockUser:
    # Placeholder para a decodificação do JWT do Supabase
    if not creds:
        # Se não tiver token, usa um usuário de demonstração ou lança um 401
        return MockUser(id="auth-user-uuid")
    
    # Em produção, usaremos jose ou jwt para validar o access_token e extrair o sub (user_id)
    return MockUser(id="auth-user-uuid")
