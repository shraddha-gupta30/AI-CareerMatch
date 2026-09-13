export interface ExtractedSkillItem {
  name: string;
  proficiency_level: 'beginner' | 'intermediate' | 'advanced' | 'expert' | string;
  years_experience: number;
  canonical_skill_id?: string | null;
  canonical_name?: string | null;
  category?: string | null;
  matched: boolean;
  proficiency_source: string;
  is_verified: boolean;
}

export interface ExtractedEducationItem {
  institution: string;
  degree: string;
  field_of_study: string;
  start_date?: string | null;
  end_date?: string | null;
  grade_gpa?: string | null;
}

export interface ExtractedExperienceItem {
  company: string;
  title: string;
  location?: string | null;
  start_date: string;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
  technologies: string[];
}

export interface ExtractedProjectItem {
  title: string;
  description: string;
  repository_url?: string | null;
  live_url?: string | null;
  technologies: string[];
}

export interface ExtractedCertificationItem {
  name: string;
  issuing_organization: string;
  issue_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
}

export interface StructuredResumeData {
  full_name?: string | null;
  headline?: string | null;
  bio?: string | null;
  target_role?: string | null;
  target_location?: string | null;
  target_employment_type?: string | null;
  total_experience_years: number;
  skills: ExtractedSkillItem[];
  education: ExtractedEducationItem[];
  experience: ExtractedExperienceItem[];
  projects: ExtractedProjectItem[];
  certifications: ExtractedCertificationItem[];
}

export interface ResumeResponse {
  id: string;
  user_id: string;
  file_name: string;
  file_size_bytes: number;
  status: 'uploaded' | 'processing' | 'pending_review' | 'applied' | 'failed' | string;
  error_message?: string | null;
  created_at: string;
}

export interface ResumeDetailResponse extends ResumeResponse {
  parsed_staging_json?: StructuredResumeData | null;
}

export interface ApplyResumeResult {
  message: string;
  profile_id: string;
  skills_applied: number;
  experience_records: number;
  education_records: number;
  project_records: number;
  certification_records: number;
}
