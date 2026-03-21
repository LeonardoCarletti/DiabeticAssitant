const API_URL: string = (import.meta.env.VITE_API_URL as string) || '';

let authToken = '';

export function setToken(token: string): void {
  authToken = token;
}

export function getToken(): string {
  return authToken;
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? 'Erro na requisicao');
  }
  return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────
export async function requestOtp(phone: string): Promise<{ message: string; status: string }> {
  return apiFetch('/api/auth/send-otp', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOtp(phone: string, code: string): Promise<{
  access_token: string;
  user_id: string;
  role: string;
}> {
  return apiFetch('/api/auth/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ phone, code }),
  });
}

// ── Chat ──────────────────────────────────────────────
export async function chatWithResearcher(message: string): Promise<{ response: string }> {
  return apiFetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

import type {
  GlucoseLogsResponse,
  GlucoseEventCreate,
  GlucoseEventOut,
  MealCreateRequest,
  MealOut,
  MealsListResponse,
} from '../types/clinical';

// ── Logs ──────────────────────────────────────────────
export async function getGlucoseLogs(params?: {
  range?: '6h' | '24h' | '7d' | '30d';
  source?: 'manual' | 'cgm' | 'all';
  granularity?: 'point' | 'hour' | 'day';
}): Promise<GlucoseLogsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.range) searchParams.set('range', params.range);
  if (params?.source) searchParams.set('source', params.source);
  if (params?.granularity) searchParams.set('granularity', params.granularity);

  const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
  return apiFetch<GlucoseLogsResponse>(`/api/logs${query}`);
}

export async function createGlucoseEvent(
  payload: GlucoseEventCreate
): Promise<GlucoseEventOut> {
  return apiFetch<GlucoseEventOut>('/api/logs/glucose', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Nutrição / Refeições ──────────────────────────────
export async function getMeals(params?: {
  range?: '24h' | '7d' | '30d';
}): Promise<MealsListResponse> {
  const q = new URLSearchParams();
  if (params?.range) q.set('range', params.range);
  return apiFetch<MealsListResponse>(`/api/nutrition/meals?${q.toString()}`);
}

export async function createMeal(
  payload: MealCreateRequest
): Promise<MealOut> {
  return apiFetch<MealOut>('/api/nutrition/meals', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Predict ────────────────────────────────────────────
export async function getPredictiveAnalysis(): Promise<{
  prediction: string;
  confidence: number;
  next_glucose: number;
  trend: string;
}> {
  return apiFetch('/api/predict');
}

// ── Workout ────────────────────────────────────────────
export async function generateWorkout(profile: {
  level: string;
  goal: string;
  glucose: string;
}): Promise<{
  title: string;
  duration: string;
  level: string;
  glucose_recommendation: string;
  exercises: Array<{ name: string; sets: string; reps: string; rest: string; notes?: string }>;
  coach_tip: string;
}> {
  return apiFetch('/api/workout/generate', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}
