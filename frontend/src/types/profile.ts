import { User } from './auth';

export interface CandidateProfile {
  id: string;
  user_id: string;
  headline: string | null;
  bio: string | null;
  target_role: string;
  target_location: string | null;
  target_employment_type: string | null;
  total_experience_years: number;
  created_at: string;
  updated_at: string;
  user?: User;
}

export interface ProfilePayload {
  target_role: string;
  headline?: string | null;
  bio?: string | null;
  target_location?: string | null;
  target_employment_type?: string | null;
  total_experience_years: number;
}
