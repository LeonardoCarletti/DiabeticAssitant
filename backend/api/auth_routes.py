from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import random
import time

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory storage for OTPs (In production, use Redis)
otp_storage = {}

class PhoneRequest(BaseModel):
    phone: str

class VerifyRequest(BaseModel):
    phone: str
    code: str

@router.post("/otp/request")
async def request_otp(payload: PhoneRequest, background_tasks: BackgroundTasks):
    # Normalize phone: remove non-digits
    phone = "".join(filter(str.isdigit, payload.phone))
    
    if not phone:
        raise HTTPException(status_code=400, detail="Número de telefone inválido")

    # Generate a 6-digit code
    code = str(random.randint(100000, 999999))
    
    # Store for 5 minutes
    otp_storage[phone] = {
        "code": code,
        "expires": time.time() + 300
    }
    
    # Mock sending SMS
    print(f"DEBUG: SMS enviado para {phone}: {code}")
    
    return {"message": "Código enviado com sucesso", "status": "sent"}

@router.post("/otp/verify")
async def verify_otp(payload: VerifyRequest):
    phone = "".join(filter(str.isdigit, payload.phone))
    
    # Master code bypass for demo/testing
    if payload.code == "000000":
        return {
            "access_token": f"elite-token-{phone}",
            "token_type": "bearer",
            "user_id": phone,
            "role": "user"
        }

    if phone not in otp_storage:
        raise HTTPException(status_code=400, detail="Código não solicitado ou expirado")
        
    stored_data = otp_storage[phone]
    
    if time.time() > stored_data["expires"]:
        del otp_storage[phone]
        raise HTTPException(status_code=400, detail="Código expirado")
        
    if payload.code != stored_data["code"]:
        raise HTTPException(status_code=400, detail="Código incorreto")
        
    # Clean up
    del otp_storage[phone]
    
    # In a real app, generate a JWT here. For now, we'll return a success token.
    return {
        "access_token": f"elite-token-{phone}",
        "token_type": "bearer",
        "user_id": phone,
        "role": "user"
    }
