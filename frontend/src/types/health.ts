export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export interface ApiError {
  message: string;
  code?: string;
}
