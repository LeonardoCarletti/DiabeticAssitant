# backend/app/routers/chat.py
import os
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.dependencies import get_supabase_client, get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Se não houver GEMINI_API_KEY no momento da compilação global, ignoramos até o runtime.
try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
except Exception:
    pass

# ── System Prompt (ADA 2024 + LGPD + guardrails) ──────────────────
_SYSTEM_PROMPT = """\
Você é o DiabeticAssistant, um assistente de saúde especializado em diabetes.

## LIMITES CRÍTICOS (NUNCA viole estes)
- Você NÃO é médico. Nunca substitua consultas médicas.
- NUNCA prescreva doses de insulina sem supervisão médica.
- Em glicose < 54 mg/dL: instrua ação de emergência IMEDIATA antes de qualquer outra coisa.
- Em glicose > 300 mg/dL: instrua busca de atendimento médico urgente.

## GUARDRAILS AUTOMÁTICOS
- Hipoglicemia severa (< 54): "⚠️ EMERGÊNCIA: Tome 15g de carb rápido agora (3 sachês de mel ou 150ml de suco). Se não melhorar em 15min, ligue 192 (SAMU)."
- Hiperglicemia grave (> 300): "⚠️ ATENÇÃO: Glicose > 300 mg/dL. Hidrate-se e contate seu médico ou vá ao pronto-socorro."

## CONTEXTO DO PACIENTE (dados reais do banco)
{patient_context}

## DIRETRIZES ADA 2024
- TIR alvo: ≥70% entre 70-180 mg/dL
- TBR alvo: <4% abaixo de 70 mg/dL (<1% abaixo de 54 mg/dL)
- TAR alvo: <25% acima de 180 mg/dL
- HbA1c geral: <7.0% (individualizar)

## ESTILO
- Linguagem clara, acolhedora, não alarmista
- Relacione respostas com dados reais do paciente sempre que relevante
- Finalize orientações clínicas com: "Converse com seu médico ou educador em diabetes sobre isso."
"""

def _format_patient_context(ctx: dict) -> str:
    profile = ctx.get("profile", {})
    tir = ctx.get("tir_14d", {})
    last_glucose = ctx.get("last_glucose")
    recent_meals = ctx.get("recent_meals") or []
    lines = []

    if profile:
        lines += [
            f"Paciente: {profile.get('full_name', 'Não informado')}",
            f"Tipo de diabetes: {profile.get('diabetes_type', 'Não informado')}",
            f"Usa insulina: {'Sim' if profile.get('insulin_user') else 'Não'}",
            f"Meta glicêmica: {profile.get('target_glucose_min', 70)}-{profile.get('target_glucose_max', 180)} mg/dL",
            f"Meta HbA1c: {profile.get('hba1c_target', 7.0)}%",
        ]

    if last_glucose:
        val = last_glucose.get("value_mg_dl")
        ts = str(last_glucose.get("measured_at", ""))[:16].replace("T", " ")
        ctx_label = last_glucose.get("context") or "sem contexto"
        flag = "⚠️ HIPO" if last_glucose.get("hypo_flag") else ("⚠️ HIPER" if last_glucose.get("hyper_flag") else "✅ Normal")
        lines.append(f"\\nÚltima glicose: {val} mg/dL ({ts}, {ctx_label}) — {flag}")

    if tir and tir.get("total_readings", 0) > 0:
        lines += [
            f"\\nTIR 14 dias ({tir.get('total_readings')} leituras):",
            f"  TIR: {tir.get('tir_percent')}%  |  TBR: {tir.get('tbr_percent')}%  |  TAR: {tir.get('tar_percent')}%",
            f"  Média: {tir.get('avg_glucose')} mg/dL  |  DP: {tir.get('std_glucose')} mg/dL",
        ]
    else:
        lines.append("\\nTIR: Sem dados suficientes ainda.")

    if recent_meals:
        lines.append("\\nÚltimas refeições:")
        for m in recent_meals[:3]:
            ts = str(m.get("eaten_at") or "")[:16].replace("T", " ")
            lines.append(
                f"  - {m.get('meal_type')} ({ts}): "
                f"{m.get('total_carbs_g', 0)}g carb, {m.get('total_calories', 0)} kcal"
            )

    return "\\n".join(lines) or "Sem dados disponíveis ainda."

class ChatMessage(BaseModel):
    role: str   # "user" | "model"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@router.post("/")
async def chat(
    req: ChatRequest,
    user=Depends(get_current_user),
    db=Depends(get_supabase_client),
):
    # 1. Buscar contexto real do paciente
    ctx_result = db.rpc("build_ai_context", {"p_user_id": str(user.id)}).execute()
    patient_ctx = ctx_result.data[0] if ctx_result.data else {}

    # 2. Guardrail de emergência (prefixo antes da resposta do LLM)
    emergency_prefix = ""
    last_glucose = patient_ctx.get("last_glucose")
    if last_glucose:
        val = float(last_glucose.get("value_mg_dl", 100))
        if val < 54:
            emergency_prefix = (
                "⚠️ EMERGÊNCIA HIPOGLICÊMICA: Sua última glicose registrada é "
                f"{val} mg/dL — abaixo de 54 mg/dL. "
                "Tome 15g de carboidratos rápidos AGORA e acione o SAMU (192) se não melhorar em 15 minutos.\\n\\n"
            )
        elif val > 300:
            emergency_prefix = (
                "⚠️ HIPERGLICEMIA GRAVE: Sua última glicose registrada é "
                f"{val} mg/dL. "
                "Hidrate-se e procure seu médico ou pronto-socorro imediatamente.\\n\\n"
            )

    # 3. Montar system prompt com contexto real
    patient_text = _format_patient_context(patient_ctx)
    system_with_ctx = _SYSTEM_PROMPT.format(patient_context=patient_text)

    # 4. Reconstruir histórico de conversa
    history = []
    for turn in (req.history or []):
        if turn.role in ("user", "model"):
            history.append({"role": turn.role, "parts": [turn.content]})

    # Reconfigura API KEY (caso tenha sido loadada pos-runtime)
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

    # 5. Chamar Gemini 2.0 Flash
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_with_ctx,
    )
    chat_session = model.start_chat(history=history)

    try:
        response = chat_session.send_message(req.message)
        reply = emergency_prefix + response.text
    except Exception as e:
        raise HTTPException(500, f"Erro no Gemini: {str(e)}")

    return {
        "reply": reply,
        "context_snapshot": {
            "last_glucose": last_glucose,
            "tir_14d": patient_ctx.get("tir_14d"),
        },
    }
