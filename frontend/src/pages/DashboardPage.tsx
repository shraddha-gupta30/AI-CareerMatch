import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigationStore } from '../store/navigationStore';
import { fetchProfile } from '../services/profile';
import { listResumes } from '../services/resumes';
import { fetchJobs, fetchSavedJobs, fetchCandidateRoadmaps } from '../services/jobs';
import { CandidateProfile } from '../types/profile';
import { ResumeResponse } from '../types/resume';
import { JobItem, SavedJobItem, Roadmap } from '../types/job';
import { DashboardMetricCard } from '../components/dashboard/DashboardMetricCard';
import { PipelineTracker } from '../components/dashboard/PipelineTracker';
import {
  Compass,
  Briefcase,
  User,
  FileText,
  ArrowRight,
  Sparkles,
  Bookmark,
  TrendingUp,
  MapPin,
  AlertCircle,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, token } = useAuthStore();
  const { navigate, navigateToJob } = useNavigationStore();

  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [totalJobs, setTotalJobs] = useState(0);
  const [savedJobs, setSavedJobs] = useState<SavedJobItem[]>([]);
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      const [
        profileRes,
        resumesRes,
        jobsRes,
        savedJobsRes,
        roadmapsRes,
      ] = await Promise.allSettled([
        fetchProfile(token),
        listResumes(token),
        fetchJobs({ limit: 12 }, token),
        fetchSavedJobs(token),
        fetchCandidateRoadmaps(token),
      ]);

      if (profileRes.status === 'fulfilled') {
        setProfile(profileRes.value);
      }
      if (resumesRes.status === 'fulfilled') {
        setResumes(resumesRes.value);
      }
      if (jobsRes.status === 'fulfilled') {
        setJobs(jobsRes.value.items || []);
        setTotalJobs(jobsRes.value.total || 0);
      }
      if (savedJobsRes.status === 'fulfilled') {
        setSavedJobs(savedJobsRes.value || []);
      }
      if (roadmapsRes.status === 'fulfilled') {
        setRoadmaps(roadmapsRes.value || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [token]);

  // Derived Metrics
  // 1. Profile Completeness (0-100)
  const calculateProfileCompleteness = (): { score: number; details: string } => {
    if (!profile) return { score: 0, details: 'Create your profile to get started' };

    let score = 0;
    const missing: string[] = [];

    if (profile.target_role) score += 25;
    else missing.push('Target role');

    if (profile.total_experience_years > 0) score += 15;
    else missing.push('Experience');

    if (profile.headline && profile.bio) score += 20;
    else if (profile.headline || profile.bio) score += 10;
    else missing.push('Headline / Bio');

    if (profile.target_location && profile.target_employment_type) score += 15;
    else missing.push('Location preferences');

    const hasCompletedResume = resumes.some(
      (r) => r.status.toLowerCase() === 'completed' || r.status.toLowerCase() === 'parsed'
    );
    if (hasCompletedResume) score += 25;
    else missing.push('Resume PDF');

    const details =
      missing.length > 0
        ? `Pending: ${missing.slice(0, 2).join(', ')}`
        : 'Profile 100% complete';

    return { score, details };
  };

  const { score: profileScore, details: profileDetails } = calculateProfileCompleteness();

  // 2. Top Matched Jobs (sorted descending by match_score)
  const sortedMatchedJobs = [...jobs]
    .filter((j) => typeof j.match_score === 'number')
    .sort((a, b) => (b.match_score || 0) - (a.match_score || 0));

  const bestMatch = sortedMatchedJobs.length > 0 ? sortedMatchedJobs[0] : null;
  const bestMatchScore = bestMatch?.match_score ? `${bestMatch.match_score.toFixed(0)}%` : 'N/A';

  // 3. Active Roadmap
  const primaryRoadmap = roadmaps.length > 0 ? roadmaps[0] : null;
  const roadmapPercentage = primaryRoadmap?.progress?.progress_percentage ?? 0;
  const roadmapCompletedItems = primaryRoadmap?.progress?.completed_items ?? 0;
  const roadmapTotalItems = primaryRoadmap?.progress?.total_items ?? 0;

  // 4. Latest Resume
  const latestResume = resumes.length > 0 ? resumes[0] : null;

  // Pipeline Status
  const pipelineStages = {
    hasProfile: Boolean(profile && profile.target_role),
    hasResume: resumes.length > 0,
    hasViewedJobs: jobs.length > 0,
    hasSimulated: Boolean(profile && jobs.length > 0),
    hasRoadmap: roadmaps.length > 0,
  };

  if (isLoading) {
    return (
      <div className="space-y-8 animate-pulse">
        {/* Skeleton Hero */}
        <div className="h-36 bg-slate-200 rounded-2xl" />

        {/* Skeleton Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-2xl" />
          ))}
        </div>

        {/* Skeleton Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <div className="h-48 bg-slate-200 rounded-2xl" />
            <div className="h-64 bg-slate-200 rounded-2xl" />
          </div>
          <div className="lg:col-span-4 space-y-6">
            <div className="h-64 bg-slate-200 rounded-2xl" />
            <div className="h-48 bg-slate-200 rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 1. Executive Hero Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 rounded-3xl shadow-lg border border-slate-800">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/20 text-sky-300 text-xs font-semibold mb-3 border border-sky-400/30">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Candidate Career Command Center</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Welcome back, {user?.full_name || 'Candidate'}
            </h1>

            <p className="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              {profile?.target_role ? (
                <>
                  Tracking career readiness for{' '}
                  <span className="text-sky-300 font-semibold">{profile.target_role}</span>
                  {profile.target_location ? ` in ${profile.target_location}` : ''}.
                </>
              ) : (
                'Set your career target and upload your resume to unlock deterministic job matching.'
              )}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/jobs')}
              className="inline-flex items-center space-x-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white rounded-xl text-xs font-semibold shadow-sm transition"
            >
              <Briefcase className="w-4 h-4" />
              <span>Explore Catalog ({totalJobs})</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/resume')}
              className="inline-flex items-center space-x-2 px-4 py-2.5 bg-white/10 hover:bg-white/20 active:bg-white/25 border border-white/20 text-white rounded-xl text-xs font-semibold transition"
            >
              <FileText className="w-4 h-4" />
              <span>Resume Review</span>
            </button>
          </div>
        </div>

        {/* Decorative subtle background accents */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-16 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Error Notice if any */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={loadDashboardData}
            className="flex items-center space-x-1 font-semibold text-rose-700 hover:text-rose-900 ml-4"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* 2. Key Metrics Row (4 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardMetricCard
          title="Profile Completeness"
          value={`${profileScore}%`}
          subtitle={profileDetails}
          icon={User}
          iconColor="text-indigo-600"
          iconBg="bg-indigo-50"
          badge={{
            text: profileScore === 100 ? 'Complete' : 'In Progress',
            variant: profileScore === 100 ? 'emerald' : 'sky',
          }}
          progress={{
            current: profileScore,
            max: 100,
            percentage: profileScore,
          }}
          onClick={() => navigate('/profile')}
          ctaText="Manage Profile"
        />

        <DashboardMetricCard
          title="Best Match Score"
          value={bestMatchScore}
          subtitle={bestMatch ? `${bestMatch.title} at ${bestMatch.company}` : 'Evaluate jobs catalog'}
          icon={TrendingUp}
          iconColor="text-emerald-600"
          iconBg="bg-emerald-50"
          badge={
            bestMatch
              ? { text: 'Top Match', variant: 'emerald' }
              : { text: 'Pending', variant: 'slate' }
          }
          onClick={() => {
            if (bestMatch) {
              navigateToJob(bestMatch.id, 'match');
            } else {
              navigate('/jobs');
            }
          }}
          ctaText={bestMatch ? 'Inspect Match Breakdown' : 'Browse Catalog'}
        />

        <DashboardMetricCard
          title="Career Roadmap"
          value={primaryRoadmap ? `${roadmapPercentage.toFixed(0)}%` : 'None'}
          subtitle={
            primaryRoadmap
              ? `${roadmapCompletedItems} of ${roadmapTotalItems} milestones reached`
              : 'Generate from top job gap'
          }
          icon={Compass}
          iconColor="text-sky-600"
          iconBg="bg-sky-50"
          badge={
            primaryRoadmap
              ? { text: `${roadmapCompletedItems}/${roadmapTotalItems} Done`, variant: 'indigo' }
              : { text: 'Available', variant: 'slate' }
          }
          onClick={() => {
            if (primaryRoadmap && primaryRoadmap.target_job_id) {
              navigateToJob(primaryRoadmap.target_job_id, 'roadmap');
            } else if (bestMatch) {
              navigateToJob(bestMatch.id, 'roadmap');
            } else {
              navigate('/jobs');
            }
          }}
          ctaText={primaryRoadmap ? 'Continue Roadmap' : 'Create Roadmap'}
        />

        <DashboardMetricCard
          title="Saved Positions"
          value={savedJobs.length}
          subtitle={`${totalJobs} curated opportunities available`}
          icon={Bookmark}
          iconColor="text-amber-600"
          iconBg="bg-amber-50"
          badge={{ text: 'Bookmarked', variant: 'amber' }}
          onClick={() => navigate('/jobs')}
          ctaText="View Saved Jobs"
        />
      </div>

      {/* 3. Main Command Center Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Roadmap Spotlight + Top Matched Jobs (8 cols) */}
        <div className="lg:col-span-8 space-y-8">
          {/* Active Roadmap Spotlight Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center">
                  <Compass className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Active Career Roadmap
                  </h3>
                  <p className="text-xs text-slate-500">
                    DAG-sequenced learning path based on your real skill gaps
                  </p>
                </div>
              </div>

              {primaryRoadmap && (
                <span className="text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-full">
                  {primaryRoadmap.target_role}
                </span>
              )}
            </div>

            {primaryRoadmap ? (
              <div className="mt-5 space-y-5">
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5 font-semibold">
                    <span className="text-slate-800">
                      Overall Progress toward{' '}
                      <span className="text-indigo-600">
                        {primaryRoadmap.target_job_title || primaryRoadmap.target_role}
                      </span>
                    </span>
                    <span className="text-indigo-600 font-bold">
                      {roadmapPercentage.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-sky-500 to-indigo-600 h-full rounded-full transition-all duration-500"
                      style={{ width: `${roadmapPercentage}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                    <span>
                      {roadmapCompletedItems} of {roadmapTotalItems} milestones completed
                    </span>
                    <span>
                      {Math.max(0, roadmapTotalItems - roadmapCompletedItems)} milestones remaining
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Target Role & Company
                    </span>
                    <h4 className="text-xs font-bold text-slate-900 mt-0.5">
                      {primaryRoadmap.target_job_title || primaryRoadmap.target_role}
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      {primaryRoadmap.target_job_company ? `At ${primaryRoadmap.target_job_company}` : 'General Career Objective'}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      if (primaryRoadmap.target_job_id) {
                        navigateToJob(primaryRoadmap.target_job_id, 'roadmap');
                      } else if (bestMatch) {
                        navigateToJob(bestMatch.id, 'roadmap');
                      } else {
                        navigate('/jobs');
                      }
                    }}
                    className="self-start sm:self-auto px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center space-x-1.5"
                  >
                    <span>Continue Roadmap</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-6 py-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300">
                <Compass className="w-10 h-10 text-indigo-500 mx-auto mb-2 opacity-80" />
                <h4 className="text-xs font-bold text-slate-900">
                  No Active Roadmap Yet
                </h4>
                <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                  Transform missing skills and prerequisite knowledge for any job into a 4-stage action plan with estimated hours and project deliverables.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    if (bestMatch) {
                      navigateToJob(bestMatch.id, 'roadmap');
                    } else {
                      navigate('/jobs');
                    }
                  }}
                  className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition inline-flex items-center space-x-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Generate Roadmap for Best Match</span>
                </button>
              </div>
            )}
          </div>

          {/* Top Job Matches (Deterministic Ranking) */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Top Recommended Matches
                </h3>
                <p className="text-xs text-slate-500">
                  Calculated with 100% deterministic mathematical scoring
                </p>
              </div>

              <button
                type="button"
                onClick={() => navigate('/jobs')}
                className="text-xs font-semibold text-sky-600 hover:text-sky-800 transition flex items-center space-x-1"
              >
                <span>View All ({totalJobs})</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {sortedMatchedJobs.length > 0 ? (
              <div className="mt-4 space-y-3">
                {sortedMatchedJobs.slice(0, 4).map((job) => {
                  const score = job.match_score || 0;
                  const scoreColor =
                    score >= 75
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : score >= 50
                      ? 'bg-sky-50 text-sky-800 border-sky-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200';

                  return (
                    <div
                      key={job.id}
                      className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm transition flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-xs font-bold text-slate-900 truncate">
                            {job.title}
                          </h4>
                          <span
                            className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${scoreColor}`}
                          >
                            {score.toFixed(0)}% Match
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 mt-1">
                          <span className="font-semibold text-slate-700">{job.company}</span>
                          <span className="flex items-center space-x-1">
                            <MapPin className="w-3 h-3 text-slate-400" />
                            <span>{job.location}</span>
                          </span>
                          <span className="capitalize">{job.employment_type}</span>
                          <span>{job.min_experience_years} yrs exp</span>
                        </div>
                      </div>

                      {/* Quick Action Buttons */}
                      <div className="flex items-center space-x-2 self-start sm:self-auto flex-shrink-0">
                        <button
                          type="button"
                          onClick={() => navigateToJob(job.id, 'match')}
                          className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[11px] font-semibold transition"
                        >
                          Breakdown
                        </button>
                        <button
                          type="button"
                          onClick={() => navigateToJob(job.id, 'gaps')}
                          className="px-2.5 py-1.5 bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 rounded-lg text-[11px] font-semibold transition"
                        >
                          Skill Gaps
                        </button>
                        <button
                          type="button"
                          onClick={() => navigateToJob(job.id, 'simulator')}
                          className="px-2.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-800 border border-indigo-200 rounded-lg text-[11px] font-semibold transition"
                        >
                          Simulator
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="mt-4 py-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <Briefcase className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-xs text-slate-600 font-medium">
                  {profile
                    ? 'No match calculations available yet. Explore the curated jobs catalog.'
                    : 'Create your career profile to see deterministic match scores.'}
                </p>
                <button
                  type="button"
                  onClick={() => navigate(profile ? '/jobs' : '/profile')}
                  className="mt-3 px-3.5 py-1.5 bg-sky-600 text-white rounded-lg text-xs font-semibold hover:bg-sky-700 transition"
                >
                  {profile ? 'Explore Jobs Catalog' : 'Create Profile'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Pipeline Stepper + Profile Snapshot (4 cols) */}
        <div className="lg:col-span-4 space-y-8">
          {/* Pipeline Stepper */}
          <PipelineTracker
            stages={pipelineStages}
            onNavigate={navigate}
            onNavigateToJobs={(tab) => {
              if (bestMatch) {
                navigateToJob(bestMatch.id, tab);
              } else {
                navigate('/jobs');
              }
            }}
          />

          {/* Candidate Profile Snapshot */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Candidate Snapshot
              </h3>
              <button
                type="button"
                onClick={() => navigate('/profile')}
                className="text-xs font-semibold text-sky-600 hover:text-sky-800 transition"
              >
                Edit
              </button>
            </div>

            {profile ? (
              <div className="space-y-3.5 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    Target Role
                  </span>
                  <p className="font-semibold text-slate-800 mt-0.5">
                    {profile.target_role}
                  </p>
                </div>

                {profile.headline && (
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">
                      Professional Headline
                    </span>
                    <p className="text-slate-700 mt-0.5">{profile.headline}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">
                      Experience
                    </span>
                    <p className="font-semibold text-slate-800 mt-0.5">
                      {profile.total_experience_years} Years
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">
                      Location
                    </span>
                    <p className="font-semibold text-slate-800 mt-0.5">
                      {profile.target_location || 'Not Specified'}
                    </p>
                  </div>
                </div>

                {/* Latest Resume Status */}
                <div className="pt-3 border-t border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold mb-1.5">
                    Active Resume
                  </span>
                  {latestResume ? (
                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
                      <div className="min-w-0 flex items-center space-x-2">
                        <FileText className="w-3.5 h-3.5 text-sky-600 flex-shrink-0" />
                        <span className="truncate text-slate-700 font-medium">
                          {latestResume.file_name}
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded capitalize">
                        {latestResume.status}
                      </span>
                    </div>
                  ) : (
                    <div className="p-2.5 rounded-lg bg-amber-50/50 border border-amber-200 flex items-center justify-between">
                      <span className="text-amber-800 text-[11px]">No resume uploaded</span>
                      <button
                        type="button"
                        onClick={() => navigate('/resume')}
                        className="text-[11px] font-semibold text-amber-900 underline"
                      >
                        Upload
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-xs text-slate-500 mb-3">
                  No career profile configured yet.
                </p>
                <button
                  type="button"
                  onClick={() => navigate('/profile')}
                  className="px-4 py-2 bg-sky-600 text-white rounded-lg text-xs font-semibold hover:bg-sky-700 transition"
                >
                  Create Profile
                </button>
              </div>
            )}
          </div>

          {/* Deterministic Architectural Integrity Card */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 to-indigo-950 text-white shadow-sm border border-slate-800">
            <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Deterministic Core</span>
            </div>
            <h4 className="text-xs font-bold text-white mb-1">
              100% Explainable Math
            </h4>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Match scores are computed deterministically using proportional weights across required and preferred skills, taxonomy relationships, and experience deltas. Zero hallucinated scoring.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
