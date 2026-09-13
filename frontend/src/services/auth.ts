import { LoginPayload, RegisterPayload, TokenResponse, User } from '../types/auth';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const body = await response.json();
      if (body.error?.message) {
        errorMessage = body.error.message;
      } else if (body.detail) {
        if (typeof body.detail === 'string') {
          errorMessage = body.detail;
        } else if (Array.isArray(body.detail) && body.detail.length > 0) {
          errorMessage = body.detail.map((d: any) => d.msg || d.message).join(', ');
        }
      }
    } catch {
      // Keep default HTTP status message if JSON parsing fails
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export async function registerUser(payload: RegisterPayload): Promise<TokenResponse> {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<TokenResponse>(response);
}

export async function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<TokenResponse>(response);
}

export async function fetchCurrentUser(token: string): Promise<User> {
  let signal: AbortSignal | undefined;
  if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
    signal = AbortSignal.timeout(8000);
  } else if (typeof AbortController !== 'undefined') {
    const controller = new AbortController();
    setTimeout(() => controller.abort(new Error('Session request timed out after 8 seconds')), 8000);
    signal = controller.signal;
  }

  const response = await fetch(`${BASE_URL}/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
    signal,
  });
  return handleResponse<User>(response);
}
