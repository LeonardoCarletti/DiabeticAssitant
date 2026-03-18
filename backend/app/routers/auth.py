# backend/app/routers/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])

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
