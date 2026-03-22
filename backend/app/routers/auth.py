# backend/app/routers/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Dev bypass phone - autenticacao facilitada
DEV_BYPASS_PHONE = "11988024265"
DEV_BYPASS_TOKEN = "dev-bypass-token-leonardo"
DEV_BYPASS_USER_ID = "dev-user-leonardo"

class AuthRequest(BaseModel):
    phone: str

class VerifyRequest(BaseModel):
    phone: str
    code: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str | None = None

@router.post("/send-otp")
async def send_otp(req: AuthRequest):
    # Bypass para telefone de desenvolvimento
    phone_clean = req.phone.replace("+55", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if phone_clean == DEV_BYPASS_PHONE or req.phone == DEV_BYPASS_PHONE:
        return {"message": "Acesso liberado (dev mode)", "demo": False, "bypass": True}
    
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if supabase_url and supabase_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.post(
                    f"{supabase_url}/auth/v1/otp",
                    headers={"apikey": supabase_key, "Content-Type": "application/json"},
                    json={"phone": req.phone}
                )
                if r.status_code == 200:
                    return {"message": "OTP enviado", "demo": False}
        except Exception as e:
            print(f"Supabase OTP error: {e}")
    return {"message": "OTP enviado (demo: use 000000)", "demo": True}

@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(req: VerifyRequest):
    # Bypass para telefone de desenvolvimento - nao precisa de OTP
    phone_clean = req.phone.replace("+55", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if phone_clean == DEV_BYPASS_PHONE or req.phone == DEV_BYPASS_PHONE:
        return AuthResponse(
            access_token=DEV_BYPASS_TOKEN,
            user_id=DEV_BYPASS_USER_ID
        )
    
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if supabase_url and supabase_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.post(
                    f"{supabase_url}/auth/v1/verify",
                    headers={"apikey": supabase_key, "Content-Type": "application/json"},
                    json={"phone": req.phone, "token": req.code, "type": "sms"}
                )
                if r.status_code == 200:
                    data = r.json()
                    return AuthResponse(
                        access_token=data.get("access_token", "demo-token"),
                        user_id=data.get("user", {}).get("id")
                    )
        except Exception as e:
            print(f"Supabase verify error: {e}")
    if req.code == "000000":
        return AuthResponse(access_token="demo-token-2024", user_id="demo-user")
    raise HTTPException(status_code=401, detail="Codigo invalido")
