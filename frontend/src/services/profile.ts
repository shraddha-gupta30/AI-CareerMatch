import { CandidateProfile, ProfilePayload } from '../types/profile';

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
      // Keep fallback
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export async function fetchProfile(token: string): Promise<CandidateProfile | null> {
  const response = await fetch(`${BASE_URL}/profile`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<CandidateProfile | null>(response);
}

export async function saveProfile(payload: ProfilePayload, token: string): Promise<CandidateProfile> {
  const response = await fetch(`${BASE_URL}/profile`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<CandidateProfile>(response);
}
