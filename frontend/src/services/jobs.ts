import {
  JobDetail,
  PaginatedJobsResponse,
  SavedJobItem,
  JobMatchBreakdown,
  JobFilterParams,
  SkillGapResponse,
  SimulationRequest,
  SimulationResponse,
  Roadmap,
  RoadmapItemStatus,
  RoadmapItemUpdateResponse,
  JobRoadmapGenerationResponse,
} from '../types/job';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const body = await response.json();
      if (body.error?.message) {
        errorMessage = body.error.code ? `[${body.error.code}] ${body.error.message}` : body.error.message;
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

export async function fetchJobs(
  params: JobFilterParams = {},
  token?: string | null
): Promise<PaginatedJobsResponse> {
  const query = new URLSearchParams();
  if (params.search) query.append('search', params.search);
  if (params.role) query.append('role', params.role);
  if (params.location) query.append('location', params.location);
  if (params.employment_type) query.append('employment_type', params.employment_type);
  if (params.experience_level) query.append('experience_level', params.experience_level);
  if (params.skill) query.append('skill', params.skill);
  if (params.saved_only) query.append('saved_only', 'true');
  if (params.page) query.append('page', String(params.page));
  if (params.limit) query.append('limit', String(params.limit));

  const headers: HeadersInit = {
    'Accept': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}/jobs?${query.toString()}`, {
    method: 'GET',
    headers,
  });
  return handleResponse<PaginatedJobsResponse>(response);
}

export async function fetchJobDetail(
  jobId: string,
  token?: string | null
): Promise<JobDetail> {
  const headers: HeadersInit = {
    'Accept': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}/jobs/${jobId}`, {
    method: 'GET',
    headers,
  });
  return handleResponse<JobDetail>(response);
}

export async function fetchJobMatch(
  jobId: string,
  token: string
): Promise<JobMatchBreakdown> {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/match`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<JobMatchBreakdown>(response);
}

export async function saveJob(
  jobId: string,
  token: string
): Promise<{ saved: boolean; job_id: string }> {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/save`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<{ saved: boolean; job_id: string }>(response);
}

export async function unsaveJob(
  jobId: string,
  token: string
): Promise<{ saved: boolean; job_id: string }> {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/save`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<{ saved: boolean; job_id: string }>(response);
}

export async function fetchSavedJobs(token: string): Promise<SavedJobItem[]> {
  const response = await fetch(`${BASE_URL}/jobs/saved`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<SavedJobItem[]>(response);
}

export async function fetchJobGaps(
  jobId: string,
  token: string
): Promise<SkillGapResponse> {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/gaps`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<SkillGapResponse>(response);
}

export async function simulateJobMatch(
  jobId: string,
  payload: SimulationRequest,
  token: string
): Promise<SimulationResponse> {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/simulate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<SimulationResponse>(response);
}

export async function fetchCandidateRoadmaps(
  token: string
): Promise<Roadmap[]> {
  const response = await fetch(`${BASE_URL}/roadmaps`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<Roadmap[]>(response);
}

export async function fetchJobRoadmap(
  jobId: string,
  token: string
): Promise<Roadmap | null> {
  const response = await fetch(`${BASE_URL}/roadmaps`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  const list = await handleResponse<Array<{ id: string; target_job_id?: string | null }>>(response);
  const existing = list.find((r) => r.target_job_id === jobId);
  if (!existing) {
    return null;
  }
  const detailResponse = await fetch(`${BASE_URL}/roadmaps/${existing.id}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<Roadmap>(detailResponse);
}

export async function generateJobRoadmap(
  jobId: string,
  token: string
): Promise<JobRoadmapGenerationResponse> {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/roadmap`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
    },
  });
  return handleResponse<JobRoadmapGenerationResponse>(response);
}

export async function updateRoadmapItemStatus(
  roadmapId: string,
  itemId: string,
  status: RoadmapItemStatus,
  token: string
): Promise<RoadmapItemUpdateResponse> {
  const response = await fetch(`${BASE_URL}/roadmaps/${roadmapId}/items/${itemId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ status }),
  });
  return handleResponse<RoadmapItemUpdateResponse>(response);
}


