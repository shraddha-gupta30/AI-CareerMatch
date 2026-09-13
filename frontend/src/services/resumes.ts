import {
  ResumeResponse,
  ResumeDetailResponse,
  StructuredResumeData,
  ApplyResumeResult,
} from '../types/resume';

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
      // Fallback
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export async function uploadResume(file: File, token: string): Promise<ResumeDetailResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/resumes`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
      // Note: do not set Content-Type header manually when sending FormData so browser sets boundary
    },
    body: formData,
  });

  return handleResponse<ResumeDetailResponse>(response);
}

export async function listResumes(token: string): Promise<ResumeResponse[]> {
  const response = await fetch(`${BASE_URL}/resumes`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });

  return handleResponse<ResumeResponse[]>(response);
}

export async function getResumeDetail(id: string, token: string): Promise<ResumeDetailResponse> {
  const response = await fetch(`${BASE_URL}/resumes/${id}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });

  return handleResponse<ResumeDetailResponse>(response);
}

export async function deleteResume(id: string, token: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${BASE_URL}/resumes/${id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });

  return handleResponse<{ success: boolean; message: string }>(response);
}

export async function applyResumeDraft(
  id: string,
  draft: StructuredResumeData,
  token: string
): Promise<ApplyResumeResult> {
  const response = await fetch(`${BASE_URL}/resumes/${id}/apply`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(draft),
  });

  return handleResponse<ApplyResumeResult>(response);
}
