const API_URL: string = (import.meta.env.VITE_API_URL as string) || '';

let authToken = '';

export function setToken(token: string): void {
  authToken = token;
}

export function getToken(): string {
  return authToken;
}

type ApiResponse = Record<string, unknown>;

async function apiFetch(path: string, options: RequestInit = {}): Promise<ApiResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? 'Erro na requisicao');
  }
  return res.json() as Promise<ApiResponse>;
}

export function requestOtp(phone: string): Promise<ApiResponse> {
  return apiFetch('/auth/otp/request', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export function verifyOtp(phone: string, code: string): Promise<ApiResponse> {
  return apiFetch('/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ phone, code }),
  });
}
