// ============================================================
// BLOCO 6C — Tipos clínicos globais
// Arquivo: frontend/src/types/clinical.ts
// ============================================================

export type SourceType    = 'manual' | 'cgm' | 'lab' | 'other'
export type TrendType     = 'falling' | 'rising' | 'stable' | 'unknown'
export type ContextType   =
  | 'fasting' | 'pre_meal' | 'post_meal'
  | 'pre_workout' | 'post_workout'
  | 'bedtime' | 'random' | 'other'
export type MealType      = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'other'
export type GlucoseRelation =
  | 'pre_meal' | 'post_meal_1h' | 'post_meal_2h' | 'post_meal_other'

// --- Glicemia ---

export interface GlucoseEventCreate {
  value_mg_dl:    number
  measured_at:    string   // ISO 8601
  source?:        SourceType
  device_id?:     string
  context?:       ContextType
  notes?:         string
  correlation_id?: string
}

export interface GlucoseEventOut {
  id:          string
  measured_at: string
  value_mg_dl: number
  trend:       TrendType
  source:      SourceType
  context:     ContextType
  hypo_flag:   boolean
  hyper_flag:  boolean
  notes?:      string
}

export interface TimeInRangeMetrics {
  target_min_mg_dl:    number
  target_max_mg_dl:    number
  percent_in_range:    number
  percent_below_range: number
  percent_above_range: number
}

export interface GlucoseMetrics {
  count_events:  number
  avg_mg_dl:     number | null
  min_mg_dl:     number | null
  max_mg_dl:     number | null
  time_in_range?: TimeInRangeMetrics
  distribution?: {
    manual_count: number
    cgm_count:    number
  }
}

export interface GlucoseLogsResponse {
  range:          string
  granularity:    'point' | 'hour' | 'day'
  glucose_events: GlucoseEventOut[]
  metrics:        GlucoseMetrics
}

// --- Nutrição ---

export interface MealItemIn {
  name:       string
  carbs_g?:   number
  protein_g?: number
  fat_g?:     number
  portion?:   string
}

export interface MealItemOut extends MealItemIn {
  id: string
}

export interface LinkedGlucoseEventIn {
  glucose_event_id: string
  relation:         GlucoseRelation
}

export interface MealCreateRequest {
  name?:                 string
  meal_type?:            MealType
  eaten_at:              string   // ISO 8601
  total_carbs_g?:        number
  total_protein_g?:      number
  total_fat_g?:          number
  estimated?:            boolean
  notes?:                string
  items?:                MealItemIn[]
  linked_glucose_events?: LinkedGlucoseEventIn[]
}

export interface MealOut {
  id:             string
  user_id:        string
  name?:          string
  meal_type:      MealType
  eaten_at:       string
  total_carbs_g?: number
  total_protein_g?: number
  total_fat_g?:   number
  estimated:      boolean
  notes?:         string
  items:          MealItemOut[]
}

export interface MealsListResponse {
  range: string
  meals: MealOut[]
}
