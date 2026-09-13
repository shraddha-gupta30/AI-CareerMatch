export interface JobSkill {
  id: string;
  skill_id: string;
  name: string;
  category?: string | null;
  is_required: boolean;
  importance_weight: number;
  min_proficiency: string;
}

export interface JobItem {
  id: string;
  title: string;
  company: string;
  location: string;
  employment_type: string;
  experience_level: string;
  min_experience_years: number;
  target_education_level: string;
  description: string;
  salary_range?: string | null;
  is_active: boolean;
  created_at: string;
  skills: JobSkill[];
  is_saved: boolean;
  match_score?: number | null;
}

export interface EducationCompatibility {
  candidate_highest_level: string;
  required_level: string;
  meets_requirement: boolean;
  score: number;
  explanation: string;
}

export interface MatchedSkillDetail {
  name: string;
  candidate_proficiency: string;
  required_proficiency: string;
  importance_weight: number;
  credit: number;
  is_exact: boolean;
  confidence: number;
  is_required: boolean;
}

export interface PartialSkillDetail {
  job_skill_name: string;
  candidate_skill_name: string;
  similarity_weight: number;
  credit: number;
  candidate_proficiency: string;
  required_proficiency: string;
  is_required: boolean;
}

export interface MissingSkillDetail {
  name: string;
  required_proficiency: string;
  importance_weight: number;
  is_required: boolean;
}

export interface JobMatchBreakdown {
  overall_score: number;
  required_skills_score: number;
  preferred_skills_score: number | null;
  experience_score: number;
  education_score: number;
  matched_skills: MatchedSkillDetail[];
  partial_skills: PartialSkillDetail[];
  missing_required_skills: MissingSkillDetail[];
  missing_preferred_skills: MissingSkillDetail[];
  experience_gap: number;
  experience_gap_text: string;
  education_compatibility: {
    candidate_highest_level: string;
    required_level: string;
    meets_requirement: boolean;
    score: number;
    explanation: string;
  };
  total_required_skills_count: number;
  matched_required_skills_count: number;
  total_preferred_skills_count: number;
  matched_preferred_skills_count: number;
  active_weights: Record<string, number>;
  explanation: string;
}

export interface JobDetail extends JobItem {
  cached_match?: JobMatchBreakdown | null;
}

export interface PaginatedJobsResponse {
  items: JobItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface SavedJobItem {
  id: string;
  job_id: string;
  created_at: string;
  job: JobItem;
}

export interface JobFilterParams {
  search?: string;
  role?: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  skill?: string;
  saved_only?: boolean;
  page?: number;
  limit?: number;
}
