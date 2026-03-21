"""Rotas de Logs de Glicemia - GET e POST para o Dashboard."""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/logs", tags=["Logs de Glicemia"])


class GlucoseEventCreate(BaseModel):
    value: float
    source: str = "manual"  # manual | cgm
    notes: Optional[str] = None
    recorded_at: Optional[str] = None


class GlucoseEventOut(BaseModel):
    id: str
    value: float
    source: str
    notes: Optional[str] = None
    recorded_at: str
    user_id: str


# ── GET /api/logs ────────────────────────────────────────────────
@router.get("")
async def get_glucose_logs(
    range: Optional[str] = Query(default="24h", description="6h | 24h | 7d | 30d"),
    source: Optional[str] = Query(default="all", description="manual | cgm | all"),
    granularity: Optional[str] = Query(default="point", description="point | hour | day"),
):
    """Retorna logs de glicemia para o Dashboard.
    
    Por enquanto retorna dados mock para o frontend funcionar.
    Conectar ao banco Supabase quando necessario.
    """
    # Gera pontos de dados mock para demonstracao
    now = datetime.utcnow()
    
    # Define janela de tempo
    range_map = {
        "6h": 6,
        "24h": 24,
        "7d": 24 * 7,
        "30d": 24 * 30,
    }
    hours = range_map.get(range, 24)
    
    # Dados mock (substitua por query ao banco real)
    import random
    readings = []
    for i in range(min(hours, 48)):  # max 48 pontos
        ts = now - timedelta(hours=hours - i * (hours / min(hours, 48)))
        base_glucose = 110
        variation = random.uniform(-20, 30)
        readings.append({
            "id": f"mock-{i}",
            "value": round(base_glucose + variation, 1),
            "source": "manual",
            "recorded_at": ts.isoformat() + "Z",
            "user_id": "demo",
        })
    
    # Calcula estatisticas
    values = [r["value"] for r in readings]
    current = values[-1] if values else 0
    avg = sum(values) / len(values) if values else 0
    in_range = sum(1 for v in values if 70 <= v <= 180)
    pct_in_range = round(in_range / len(values) * 100, 1) if values else 0
    
    # Calcula tendencia
    if len(values) >= 2:
        trend = "rising" if values[-1] > values[-2] + 5 else ("falling" if values[-1] < values[-2] - 5 else "stable")
    else:
        trend = "stable"
    
    return {
        "current": current,
        "trend": trend,
        "average": round(avg, 1),
        "in_range_pct": pct_in_range,
        "readings": readings,
        "range": range,
        "source": source,
        "granularity": granularity,
    }


# ── POST /api/logs/glucose ────────────────────────────────────────
@router.post("/glucose")
async def create_glucose_event(payload: GlucoseEventCreate):
    """Registra um novo evento de glicemia."""
    now = datetime.utcnow()
    event_id = f"evt-{int(now.timestamp())}"
    return {
        "id": event_id,
        "value": payload.value,
        "source": payload.source,
        "notes": payload.notes,
        "recorded_at": (payload.recorded_at or now.isoformat() + "Z"),
        "user_id": "demo",
        "status": "saved",
    }
