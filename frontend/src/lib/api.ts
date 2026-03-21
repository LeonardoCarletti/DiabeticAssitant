// ── Base config ─────────────────────────────────────────────────
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

// ── Auth ─────────────────────────────────────────────────────────
export async function requestOtp(phone: string): Promise<{ message: string; status: string }> {
  return apiFetch('/api/auth/otp/request', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOtp(phone: string, code: string): Promise<{
  access_token: string;
  user_id: string;
  role: string;
}> {
  return apiFetch('/api/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ phone, code }),
  });
}

// ── Chat ─────────────────────────────────────────────────────────
export async function chatWithResearcher(message: string): Promise<{ response: string }> {
  return apiFetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

// ── RAG ─────────────────────────────────────────────────────────
export async function ragQuery(question: string): Promise<{ answer: string; sources?: string[] }> {
  return apiFetch('/api/rag/query', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}

// ── Perfil ───────────────────────────────────────────────────────
export async function getProfile(): Promise<Record<string, unknown>> {
  return apiFetch('/api/profile');
}

export async function createProfile(data: Record<string, unknown>): Promise<Record<string, unknown>> {
  return apiFetch('/api/profile', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProfile(data: Record<string, unknown>): Promise<Record<string, unknown>> {
  return apiFetch('/api/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ── Logs de Glicose ──────────────────────────────────────────────
import type {
  GlucoseLogsResponse,
  GlucoseEventCreate,
  GlucoseEventOut,
  MealCreateRequest,
  MealOut,
  MealsListResponse,
} from '../types/clinical';

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
  return apiFetch(`/api/logs${query}`);
}

export async function createGlucoseEvent(
  payload: GlucoseEventCreate
): Promise<GlucoseEventOut> {
  return apiFetch('/api/logs/glucose', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Nutricao / Refeicoes ─────────────────────────────────────────
export async function getMeals(params?: {
  range?: '24h' | '7d' | '30d';
}): Promise<MealsListResponse> {
  const q = new URLSearchParams();
  if (params?.range) q.set('range', params.range);
  return apiFetch(`/api/nutrition/meals?${q.toString()}`);
}

export async function createMeal(
  payload: MealCreateRequest
): Promise<MealOut> {
  return apiFetch('/api/nutrition/meals', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Predict ──────────────────────────────────────────────────────
export async function getPredictiveAnalysis(): Promise<{
  prediction: string;
  confidence: number;
  next_glucose: number;
  trend: string;
}> {
  return apiFetch('/api/predict');
}

// ── Workout ──────────────────────────────────────────────────────
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

// ── Exames ───────────────────────────────────────────────────────
export async function getExams(): Promise<Record<string, unknown>[]> {
  return apiFetch('/api/exam');
}

export async function uploadExam(formData: FormData): Promise<Record<string, unknown>> {
  // Upload multipart - sem Content-Type para o browser definir o boundary
  const res = await fetch(`${API_URL}/api/exam/upload`, {
    method: 'POST',
    headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {},
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? 'Erro no upload');
  }
  return res.json();
}

// ── Report ───────────────────────────────────────────────────────
export async function getReport(params?: { period?: string }): Promise<{ report: string }> {
  const q = new URLSearchParams();
  if (params?.period) q.set('period', params.period);
  return apiFetch(`/api/report?${q.toString()}`);
}

// ── Sync ─────────────────────────────────────────────────────────
export async function syncData(): Promise<{ status: string; message: string }> {
  return apiFetch('/api/sync', { method: 'POST' });
}

// ── Autonomo ─────────────────────────────────────────────────────
export async function getAutonomousInsights(): Promise<{ insights: string[] }> {
  return apiFetch('/api/autonomous/insights');
}

// ── Recovery ─────────────────────────────────────────────────────
export async function getRecoveryPlan(): Promise<{ plan: string }> {
  return apiFetch('/api/recovery/plan');
}

// ── Automation ───────────────────────────────────────────────────
export async function getAutomationStatus(): Promise<{ automations: Record<string, unknown>[] }> {
  return apiFetch('/api/automation/status');
}

// ── Experiment ───────────────────────────────────────────────────
export async function getExperiments(): Promise<{ experiments: Record<string, unknown>[] }> {
  return apiFetch('/api/experiment');
}
