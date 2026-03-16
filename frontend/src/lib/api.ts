const API_URL = import.meta.env.VITE_API_URL || '';

let authToken = '';

export function setToken(token: string) {
  authToken = token;
}

export function getToken(): string {
  return authToken;
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(options.headers as Record<string, string> || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erro na requisicao');
  }
  return res.json();
}

export const requestOtp = (phone: string) =>
  apiFetch('/auth/otp/request', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });

export const verifyOtp = (phone: string, code: string) =>
  apiFetch('/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ phone, code }),
  });
