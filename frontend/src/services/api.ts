import { HealthResponse } from '../types/health';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${BASE_URL}/health`, {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Backend responded with HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}
