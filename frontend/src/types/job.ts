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

export interface MatchedSkillItem {
  name: string;
  candidate_proficiency: string;
  required_proficiency: string;
  importance_weight: number;
  credit: number;
  is_exact?: boolean;
  confidence?: number;
  is_required: boolean;
}

export interface PartialSkillItem {
  job_skill_name: string;
  candidate_skill_name: string;
  similarity_weight: number;
  credit: number;
  candidate_proficiency: string;
  required_proficiency: string;
  is_required: boolean;
}

export interface MissingSkillItem {
  name: string;
  required_proficiency: string;
  importance_weight: number;
  is_required: boolean;
}

export interface ExperienceGapDetail {
  candidate_experience_years: number;
  job_min_experience_years: number;
  experience_gap: number;
  experience_gap_text: string;
  experience_score: number;
}

export interface SkillGapResponse {
  job_id: string;
  overall_score: number;
  required_skills_score: number;
  preferred_skills_score: number | null;
  experience_score: number;
  education_score: number;

  matched_required_skills: MatchedSkillItem[];
  partial_required_skills: PartialSkillItem[];
  missing_required_skills: MissingSkillItem[];

  matched_preferred_skills: MatchedSkillItem[];
  partial_preferred_skills: PartialSkillItem[];
  missing_preferred_skills: MissingSkillItem[];

  experience_gap: ExperienceGapDetail;
  education_compatibility: EducationCompatibility;

  total_required_skills_count: number;
  matched_required_skills_count: number;
  total_preferred_skills_count: number;
  matched_preferred_skills_count: number;
  active_weights: Record<string, number>;
  explanation: string;
}

export interface SimulatedSkillInput {
  name: string;
  proficiency_level: string;
  proficiency_source?: string;
}

export interface SimulationRequest {
  add_skills?: SimulatedSkillInput[];
  modify_skills?: SimulatedSkillInput[];
  remove_skills?: string[];
  experience_years?: number;
}

export interface SimulationResponse {
  job_id: string;
  current_score: number;
  simulated_score: number;
  score_delta: number;
  current_match: JobMatchBreakdown;
  simulated_match: JobMatchBreakdown;
  changed_factors: string[];
}

export const TAXONOMY_SKILLS: string[] = [
  'Python',
  'Java',
  'JavaScript',
  'TypeScript',
  'C++',
  'Go',
  'SQL',
  'HTML',
  'CSS',
  'React',
  'Node.js',
  'FastAPI',
  'Django',
  'Flask',
  'PostgreSQL',
  'MySQL',
  'MongoDB',
  'Redis',
  'Docker',
  'Kubernetes',
  'AWS',
  'Azure',
  'GCP',
  'Git',
  'Linux',
  'GraphQL',
  'Tailwind CSS',
  'Express.js',
  'Vue.js',
  'Next.js',
  'REST API',
  'Pandas',
  'NumPy',
  'TensorFlow',
  'PyTorch',
  'Scikit-learn',
  'Data Analysis',
  'Data Visualization',
  'Selenium',
  'Pytest',
  'Jest',
];

// ----------------------------------------------------------------------------
// Phase 7: Personalized Career Roadmap & Progress Tracking Types
// ----------------------------------------------------------------------------

export type RoadmapItemStatus = 'not_started' | 'in_progress' | 'completed';
export type RoadmapItemPriority = 'critical' | 'high' | 'medium' | 'low';

export interface RoadmapItem {
  id: string;
  roadmap_id: string;
  skill_id?: string | null;
  skill_name?: string | null;
  title: string;
  description: string;
  stage_phase: number;
  priority: RoadmapItemPriority;
  estimated_hours: number;
  recommended_action: string;
  suggested_project?: string | null;
  status: RoadmapItemStatus;
  sequence_order: number;
  completed_at?: string | null;
  prerequisites: string[];
}

export interface RoadmapProgress {
  total_items: number;
  completed_items: number;
  in_progress_items: number;
  not_started_items: number;
  progress_percentage: number;
}

export interface Roadmap {
  id: string;
  profile_id: string;
  target_role: string;
  target_job_id?: string | null;
  target_job_title?: string | null;
  target_job_company?: string | null;
  total_items: number;
  completed_items: number;
  progress: RoadmapProgress;
  items: RoadmapItem[];
  created_at: string;
  updated_at: string;
}

export interface RoadmapItemStatusUpdate {
  status: RoadmapItemStatus;
}

export interface RoadmapItemUpdateResponse {
  item: RoadmapItem;
  roadmap_progress: RoadmapProgress;
}

export type JobRoadmapGenerationResponse = Roadmap;


