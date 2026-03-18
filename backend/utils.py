# ============================================================
# BLOCO 2.2 — Funções auxiliares
# Arquivo: backend/utils.py
# ============================================================

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

# Calcula TIR por porcentagem de pontos (versão manual)
# Quando tiver CGM, substituir pela versão que usa timedelta entre leituras
def compute_time_in_range(events: List[Dict[str, Any]]) -> Dict[str, float]:
    TARGET_MIN = 70.0
    TARGET_MAX = 180.0

    if not events:
        return {
            "target_min_mg_dl": TARGET_MIN,
            "target_max_mg_dl": TARGET_MAX,
            "percent_in_range": 0.0,
            "percent_below_range": 0.0,
            "percent_above_range": 0.0,
        }

    total   = len(events)
    below   = sum(1 for e in events if float(e["value_mg_dl"]) < TARGET_MIN)
    above   = sum(1 for e in events if float(e["value_mg_dl"]) > TARGET_MAX)
    in_rng  = total - below - above

    return {
        "target_min_mg_dl":    TARGET_MIN,
        "target_max_mg_dl":    TARGET_MAX,
        "percent_in_range":    round(in_rng * 100.0 / total, 1),
        "percent_below_range": round(below * 100.0 / total, 1),
        "percent_above_range": round(above * 100.0 / total, 1),
    }

# Calcula início da janela temporal a partir do parâmetro `range`
def get_start_time(range_str: str) -> datetime:
    now = datetime.now(timezone.utc)
    mapping = {"6h": 6, "24h": 24, "7d": 168, "30d": 720}
    hours = mapping.get(range_str, 6)
    return now - timedelta(hours=hours)

# Detecta emergência no texto do usuário (safe guard)
EMERGENCY_KEYWORDS_PT = [
    "desmaiando", "desmaiou", "desmaiei", "convulsão", "convulsionando",
    "não respondo", "nao respondo", "inconsciente", "perdi a consciência",
    "dor no peito forte", "vomitando sem parar", "não acordo", "nao acordo",
    "respiração rápida", "respiracao rapida", "cheiro de fruta na boca",
    "glicemia 40", "glicemia 35", "glicemia 30", "sangramento intenso",
]
EMERGENCY_GLUCOSE_THRESHOLD_LOW  = 54.0  # mg/dL
EMERGENCY_GLUCOSE_THRESHOLD_HIGH = 300.0  # mg/dL

def is_emergency(text: str, glucose_value: Optional[float] = None) -> bool:
    text_lower = text.lower()
    if any(kw in text_lower for kw in EMERGENCY_KEYWORDS_PT):
        return True
    if glucose_value is not None:
        if glucose_value <= EMERGENCY_GLUCOSE_THRESHOLD_LOW:
            return True
        if glucose_value >= EMERGENCY_GLUCOSE_THRESHOLD_HIGH:
            return True
    return False

EMERGENCY_RESPONSE = (
    "⚠️ ATENÇÃO: Identifiquei uma situação de emergência médica. "
    "Por favor, ligue imediatamente para o SAMU (192) ou vá ao pronto-socorro mais próximo. "
    "Se estiver com hipoglicemia grave (glicemia muito baixa), consuma 15g de carboidrato de ação rápida "
    "(1 copo de suco de laranja, 3 balas de glicose ou 1 sachê de mel) SE estiver consciente e conseguir engolir. "
    "Não tente resolver sozinho. Procure ajuda presencial AGORA."
)

def build_clinical_context(
    glucose_events: List[Dict[str, Any]],
    meals: List[Dict[str, Any]],
    current_glucose: Optional[float] = None,
) -> str:
    """
    Monta um bloco de texto estruturado com o snapshot clínico do usuário
    para ser injetado no system prompt do Gemini antes de cada resposta.
    """
    lines = ["=== DADOS CLÍNICOS DO USUÁRIO (últimas 24h) ==="]

    # Glicemia atual
    if current_glucose is not None:
        status = "NORMAL"
        if current_glucose < 70:
            status = "⚠️ HIPOGLICEMIA"
        elif current_glucose > 180:
            status = "⚠️ HIPERGLICEMIA"
        lines.append(f"Glicemia atual: {current_glucose} mg/dL — {status}")
    else:
        lines.append("Glicemia atual: não informada")

    # Métricas do histórico
    if glucose_events:
        values = [float(e["value_mg_dl"]) for e in glucose_events]
        from statistics import mean
        avg = round(mean(values), 1)
        mn  = min(values)
        mx  = max(values)
        tir = compute_time_in_range(glucose_events)
        lines.append(
            f"Histórico glicemia: média {avg} mg/dL | min {mn} | max {mx} | "
            f"TIR (70-180): {tir['percent_in_range']}% em faixa | "
            f"{tir['percent_below_range']}% abaixo | {tir['percent_above_range']}% acima"
        )
        hypo_count  = sum(1 for e in glucose_events if float(e["value_mg_dl"]) < 70)
        hyper_count = sum(1 for e in glucose_events if float(e["value_mg_dl"]) > 180)
        if hypo_count:
            lines.append(f"Eventos de HIPOGLICEMIA nas últimas 24h: {hypo_count}")
        if hyper_count:
            lines.append(f"Eventos de HIPERGLICEMIA nas últimas 24h: {hyper_count}")
    else:
        lines.append("Histórico glicemia: sem leituras registradas nas últimas 24h.")

    # Refeições do dia
    if meals:
        total_carbs   = sum(float(m.get("total_carbs_g", 0) or 0) for m in meals)
        total_protein = sum(float(m.get("total_protein_g", 0) or 0) for m in meals)
        total_fat     = sum(float(m.get("total_fat_g", 0) or 0) for m in meals)
        lines.append(
            f"Refeições do dia: {len(meals)} registradas | "
            f"Carboidratos totais: {round(total_carbs,1)}g | "
            f"Proteínas: {round(total_protein,1)}g | "
            f"Gorduras: {round(total_fat,1)}g"
        )
        # últimas 2 refeições para contexto
        for m in meals[-2:]:
            name = m.get("name") or m.get("meal_type", "Refeição")
            carbs = m.get("total_carbs_g")
            eaten = m.get("eaten_at", "")[:16].replace("T", " ")
            lines.append(f"  - {name} ({eaten}): {carbs}g carboidratos")
    else:
        lines.append("Refeições do dia: nenhuma registrada.")

    lines.append("=== FIM DOS DADOS CLÍNICOS ===")
    return "\n".join(lines)
