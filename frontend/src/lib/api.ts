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

interface OtpRequestResponse { message: string }
interface OtpVerifyResponse { access_token: string; user_id?: string }
interface ChatResponse { response: string }
interface LogEntry { id: number; timestamp: string; value: number }
interface PredictiveResponse { prediction: string; confidence: number }

export function requestOtp(phone: string): Promise<OtpRequestResponse> {
  return apiFetch<OtpRequestResponse>('/auth/otp/request', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export function verifyOtp(phone: string, code: string): Promise<OtpVerifyResponse> {
  return apiFetch<OtpVerifyResponse>('/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ phone, code }),
  });
}

export function chatWithResearcher(message: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export function getLogs(): Promise<LogEntry[]> {
  return apiFetch<LogEntry[]>('/api/logs');
}

export function getPredictiveAnalysis(): Promise<PredictiveResponse> {
  return apiFetch<PredictiveResponse>('/api/predict');
}
