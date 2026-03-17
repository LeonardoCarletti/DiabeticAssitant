# ============================================================
# BLOCO 2.1 — Schemas Pydantic
# Arquivo: backend/schemas.py
# ============================================================

from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, Field

# ---- Glucose ----

SourceType = Literal["manual", "cgm", "lab", "other"]
TrendType  = Literal["falling", "rising", "stable", "unknown"]
ContextType = Literal[
    "fasting", "pre_meal", "post_meal", "pre_workout",
    "post_workout", "bedtime", "random", "other"
]
MealType          = Literal["breakfast", "lunch", "dinner", "snack", "other"]
GlucoseRelation   = Literal["pre_meal", "post_meal_1h", "post_meal_2h", "post_meal_other"]

class GlucoseEventCreate(BaseModel):
    value_mg_dl:    float
    measured_at:    datetime
    source:         SourceType = "manual"
    device_id:      Optional[str] = None
    context:        ContextType = "random"
    notes:          Optional[str] = None
    correlation_id: Optional[str] = None

class GlucoseEventOut(BaseModel):
    id:          str
    measured_at: datetime
    value_mg_dl: float
    trend:       TrendType
    source:      SourceType
    context:     ContextType
    hypo_flag:   bool
    hyper_flag:  bool
    notes:       Optional[str] = None

class TimeInRangeMetrics(BaseModel):
    target_min_mg_dl:   float
    target_max_mg_dl:   float
    percent_in_range:   float
    percent_below_range: float
    percent_above_range: float

class DistributionMetrics(BaseModel):
    manual_count: int
    cgm_count:    int

class GlucoseMetrics(BaseModel):
    count_events: int
    avg_mg_dl:    Optional[float]
    min_mg_dl:    Optional[float]
    max_mg_dl:    Optional[float]
    time_in_range:  Optional[TimeInRangeMetrics]
    distribution:   Optional[DistributionMetrics]

class GlucoseLogsResponse(BaseModel):
    range:          str
    granularity:    Literal["point", "hour", "day"]
    glucose_events: List[GlucoseEventOut]
    metrics:        GlucoseMetrics

# ---- Nutrition ----

class MealItemIn(BaseModel):
    name:      str
    carbs_g:   Optional[float] = None
    protein_g: Optional[float] = None
    fat_g:     Optional[float] = None
    portion:   Optional[str]   = None

class LinkedGlucoseEventIn(BaseModel):
    glucose_event_id: str
    relation:         GlucoseRelation

class MealCreateRequest(BaseModel):
    name:                 Optional[str]                    = None
    meal_type:            MealType                         = "other"
    eaten_at:             datetime
    total_carbs_g:        Optional[float]                  = None
    total_protein_g:      Optional[float]                  = None
    total_fat_g:          Optional[float]                  = None
    estimated:            bool                             = True
    notes:                Optional[str]                    = None
    items:                Optional[List[MealItemIn]]       = None
    linked_glucose_events: Optional[List[LinkedGlucoseEventIn]] = None

class MealItemOut(MealItemIn):
    id: str

class MealOut(BaseModel):
    id:             str
    user_id:        str
    name:           Optional[str]
    meal_type:      MealType
    eaten_at:       datetime
    total_carbs_g:  Optional[float]
    total_protein_g: Optional[float]
    total_fat_g:    Optional[float]
    estimated:      bool
    notes:          Optional[str]
    items:          List[MealItemOut] = []

class MealsListResponse(BaseModel):
    range: str
    meals: List[MealOut]
