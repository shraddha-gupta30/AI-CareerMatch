import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigationStore } from '../store/navigationStore';
import {
  fetchJobs,
  fetchJobDetail,
  fetchJobMatch,
  fetchJobGaps,
  simulateJobMatch,
  fetchJobRoadmap,
  generateJobRoadmap,
  updateRoadmapItemStatus,
  saveJob,
  unsaveJob,
} from '../services/jobs';
import {
  JobItem,
  JobDetail,
  JobMatchBreakdown,
  JobFilterParams,
  SkillGapResponse,
  SimulationRequest,
  SimulationResponse,
  Roadmap,
  RoadmapItemStatus,
} from '../types/job';
import { SkillGapAnalysis } from '../components/jobs/SkillGapAnalysis';
import { CareerSimulator } from '../components/jobs/CareerSimulator';
import { CareerRoadmap } from '../components/jobs/CareerRoadmap';
import {
  Briefcase,
  Search,
  MapPin,
  Clock,
  GraduationCap,
  Bookmark,
  BookmarkCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Sparkles,
  Award,
  FileText,
  DollarSign,
  TrendingUp,
  Sliders,
  Compass,
  AlertCircle,
} from 'lucide-react';

export const JobsPage: React.FC = () => {
  const { token, isAuthenticated } = useAuthStore();
  const { navigate, targetJobId, targetTab, clearJobTarget } = useNavigationStore();

  // State
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [totalJobs, setTotalJobs] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(10);

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [activeJobDetail, setActiveJobDetail] = useState<JobDetail | null>(null);
  const [activeMatch, setActiveMatch] = useState<JobMatchBreakdown | null>(null);

  // Phase 6B: Skill Gap Analysis state
  const [activeGaps, setActiveGaps] = useState<SkillGapResponse | null>(null);
  const [isLoadingGaps, setIsLoadingGaps] = useState(false);
  const [gapsError, setGapsError] = useState<string | null>(null);

  // Phase 6B: What-If Career Simulator state
  const [simAddedSkills, setSimAddedSkills] = useState<{ name: string; proficiency_level: string }[]>([]);
  const [simModifiedSkills, setSimModifiedSkills] = useState<{ name: string; proficiency_level: string }[]>([]);
  const [simRemovedSkills, setSimRemovedSkills] = useState<string[]>([]);
  const [simExperienceYears, setSimExperienceYears] = useState<number | ''>('');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simResult, setSimResult] = useState<SimulationResponse | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  // Phase 7: Career Roadmap state
  const [activeRoadmap, setActiveRoadmap] = useState<Roadmap | null>(null);
  const [isLoadingRoadmap, setIsLoadingRoadmap] = useState(false);
  const [isGeneratingRoadmap, setIsGeneratingRoadmap] = useState(false);
  const [roadmapError, setRoadmapError] = useState<string | null>(null);
  const [updatingItemId, setUpdatingItemId] = useState<string | null>(null);

  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isLoadingMatch, setIsLoadingMatch] = useState(false);

  const [errorNotice, setErrorNotice] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [noProfileNotice, setNoProfileNotice] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState('');
  const [experienceLevelFilter, setExperienceLevelFilter] = useState('');
  const [savedOnlyFilter, setSavedOnlyFilter] = useState(false);

  // Active view tab in detail view
  const [detailTab, setDetailTab] = useState<'overview' | 'match' | 'gaps' | 'simulator' | 'roadmap'>('match');

  // Load jobs list
  const loadJobs = async (page: number = 1) => {
    setIsLoadingJobs(true);
    setErrorNotice(null);
    try {
      const params: JobFilterParams = {
        search: searchTerm || undefined,
        location: locationFilter || undefined,
        employment_type: employmentTypeFilter || undefined,
        experience_level: experienceLevelFilter || undefined,
        saved_only: savedOnlyFilter || undefined,
        page,
        limit: pageSize,
      };
      const data = await fetchJobs(params, token);
      setJobs(data.items);
      setTotalJobs(data.total);
      setCurrentPage(data.page);
      setTotalPages(data.pages);

      // Auto-select first job if none selected and no external target pending
      if (data.items.length > 0 && !selectedJobId && !targetJobId) {
        selectJob(data.items[0].id);
      } else if (data.items.length === 0) {
        setActiveJobDetail(null);
        setActiveMatch(null);
      }
    } catch (err) {
      setErrorNotice(err instanceof Error ? err.message : 'Failed to load job listings.');
    } finally {
      setIsLoadingJobs(false);
    }
  };

  // Trigger search on filter changes or auth session update
  useEffect(() => {
    loadJobs(1);
  }, [searchTerm, locationFilter, employmentTypeFilter, experienceLevelFilter, savedOnlyFilter, token, isAuthenticated]);

  // Handle external navigation target (e.g. from Dashboard)
  useEffect(() => {
    if (targetJobId) {
      selectJob(targetJobId);
      if (targetTab) {
        setDetailTab(targetTab);
      }
      clearJobTarget();
    }
  }, [targetJobId, targetTab]);

  // Select job
  const selectJob = async (id: string) => {
    setSelectedJobId(id);
    setIsLoadingDetail(true);
    setErrorNotice(null);
    setNoProfileNotice(false);
    setGapsError(null);
    setSimError(null);
    setSimResult(null);
    setSimAddedSkills([]);
    setSimModifiedSkills([]);
    setSimRemovedSkills([]);
    setSimExperienceYears('');
    setActiveRoadmap(null);
    setRoadmapError(null);

    try {
      const detail = await fetchJobDetail(id, token);
      setActiveJobDetail(detail);

      if (detail.cached_match) {
        setActiveMatch(detail.cached_match as JobMatchBreakdown);
      } else if (isAuthenticated && token) {
        // Load or calculate match
        setIsLoadingMatch(true);
        try {
          const matchData = await fetchJobMatch(id, token);
          setActiveMatch(matchData);
        } catch (matchErr: any) {
          const isProfileRequired =
            matchErr.message?.includes('PROFILE_REQUIRED') ||
            matchErr.message?.toLowerCase().includes('profile');
          if (isProfileRequired) {
            setNoProfileNotice(true);
            setActiveMatch(null);
          } else {
            // Match calculation error
            setActiveMatch(null);
          }
        } finally {
          setIsLoadingMatch(false);
        }
      } else {
        setActiveMatch(null);
      }

      // Load gaps if authenticated
      if (isAuthenticated && token) {
        setIsLoadingGaps(true);
        try {
          const gapsData = await fetchJobGaps(id, token);
          setActiveGaps(gapsData);
          setSimExperienceYears(gapsData.experience_gap.candidate_experience_years);
        } catch (gapErr: any) {
          const isProfileRequired =
            gapErr.message?.includes('PROFILE_REQUIRED') ||
            gapErr.message?.toLowerCase().includes('profile');
          if (isProfileRequired) {
            setNoProfileNotice(true);
          } else {
            setGapsError(gapErr.message || 'Failed to load skill gap analysis.');
          }
          setActiveGaps(null);
        } finally {
          setIsLoadingGaps(false);
        }

        // Load existing roadmap if available
        setIsLoadingRoadmap(true);
        fetchJobRoadmap(id, token)
          .then((rm) => {
            setActiveRoadmap(rm);
          })
          .catch(() => {
            setActiveRoadmap(null);
          })
          .finally(() => {
            setIsLoadingRoadmap(false);
          });
      } else {
        setActiveGaps(null);
        setActiveRoadmap(null);
      }
    } catch (err) {
      setErrorNotice(err instanceof Error ? err.message : 'Failed to load job details.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Phase 7: Roadmap handlers
  const handleGenerateRoadmap = async () => {
    if (!selectedJobId || !token) {
      if (!isAuthenticated) {
        navigate('/login');
      }
      return;
    }
    setIsGeneratingRoadmap(true);
    setRoadmapError(null);
    try {
      const rm = await generateJobRoadmap(selectedJobId, token);
      setActiveRoadmap(rm);
      setDetailTab('roadmap');
      setActionNotice(`Personalized career roadmap generated with ${rm.total_items} milestones.`);
      setTimeout(() => setActionNotice(null), 4000);
    } catch (err: any) {
      const msg = err instanceof Error ? err.message : 'Failed to generate career roadmap.';
      if (msg.includes('PROFILE_REQUIRED') || msg.toLowerCase().includes('profile')) {
        setNoProfileNotice(true);
      } else {
        setRoadmapError(msg);
      }
    } finally {
      setIsGeneratingRoadmap(false);
    }
  };

  const handleRoadmapStatusChange = async (itemId: string, newStatus: RoadmapItemStatus) => {
    if (!activeRoadmap || !token) return;
    setUpdatingItemId(itemId);
    try {
      const res = await updateRoadmapItemStatus(activeRoadmap.id, itemId, newStatus, token);
      setActiveRoadmap((prev) => {
        if (!prev) return prev;
        const updatedItems = prev.items.map((it) =>
          it.id === itemId ? res.item : it
        );
        return {
          ...prev,
          items: updatedItems,
          completed_items: res.roadmap_progress.completed_items,
          total_items: res.roadmap_progress.total_items,
          progress: res.roadmap_progress,
          updated_at: new Date().toISOString(),
        };
      });
    } catch (err: any) {
      setRoadmapError(err instanceof Error ? err.message : 'Failed to update milestone status.');
    } finally {
      setUpdatingItemId(null);
    }
  };

  // Simulator handlers
  const handleAddSkill = (skill: { name: string; proficiency_level: string }) => {
    setSimAddedSkills((prev) => {
      const filtered = prev.filter((s) => s.name.toLowerCase() !== skill.name.toLowerCase());
      return [...filtered, skill];
    });
  };

  const handleRemoveAddedSkill = (name: string) => {
    setSimAddedSkills((prev) => prev.filter((s) => s.name.toLowerCase() !== name.toLowerCase()));
  };

  const handleModifySkill = (skill: { name: string; proficiency_level: string }) => {
    setSimModifiedSkills((prev) => {
      const filtered = prev.filter((s) => s.name.toLowerCase() !== skill.name.toLowerCase());
      return [...filtered, skill];
    });
  };

  const handleRemoveModifiedSkill = (name: string) => {
    setSimModifiedSkills((prev) => prev.filter((s) => s.name.toLowerCase() !== name.toLowerCase()));
  };

  const handleToggleRemoveSkill = (name: string) => {
    setSimRemovedSkills((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  const handleChangeExperience = (years: number | '') => {
    setSimExperienceYears(years);
  };

  const handleRunSimulation = async () => {
    if (!selectedJobId || !token) return;
    setIsSimulating(true);
    setSimError(null);

    try {
      const payload: SimulationRequest = {};
      if (simAddedSkills.length > 0) {
        payload.add_skills = simAddedSkills.map((s) => ({
          name: s.name,
          proficiency_level: s.proficiency_level,
          proficiency_source: 'user_verified',
        }));
      }
      if (simModifiedSkills.length > 0) {
        payload.modify_skills = simModifiedSkills.map((s) => ({
          name: s.name,
          proficiency_level: s.proficiency_level,
        }));
      }
      if (simRemovedSkills.length > 0) {
        payload.remove_skills = simRemovedSkills;
      }
      if (typeof simExperienceYears === 'number' && simExperienceYears >= 0) {
        payload.experience_years = simExperienceYears;
      }

      const res = await simulateJobMatch(selectedJobId, payload, token);
      setSimResult(res);
    } catch (err: any) {
      const isProfileRequired =
        err.message?.includes('PROFILE_REQUIRED') ||
        err.message?.toLowerCase().includes('profile');
      if (isProfileRequired) {
        setNoProfileNotice(true);
      } else {
        setSimError(err.message || 'Simulation failed to run.');
      }
    } finally {
      setIsSimulating(false);
    }
  };

  const handleResetScenario = () => {
    setSimAddedSkills([]);
    setSimModifiedSkills([]);
    setSimRemovedSkills([]);
    const baselineExp = activeGaps?.experience_gap.candidate_experience_years;
    setSimExperienceYears(typeof baselineExp === 'number' ? baselineExp : '');
    setSimResult(null);
    setSimError(null);
  };

  const handleQuickSimulateAddSkill = (skillName: string, reqProf: string) => {
    handleAddSkill({ name: skillName, proficiency_level: reqProf || 'intermediate' });
    setDetailTab('simulator');
  };

  // Toggle Save Job
  const handleToggleSave = async (jobId: string, currentlySaved: boolean) => {
    if (!isAuthenticated || !token) {
      navigate('/login');
      return;
    }
    try {
      if (currentlySaved) {
        await unsaveJob(jobId, token);
        setActionNotice('Job removed from bookmarks.');
      } else {
        await saveJob(jobId, token);
        setActionNotice('Job saved to your bookmarks!');
      }

      // Update state locally
      setJobs((prev) =>
        prev.map((j) => (j.id === jobId ? { ...j, is_saved: !currentlySaved } : j))
      );
      if (activeJobDetail && activeJobDetail.id === jobId) {
        setActiveJobDetail({ ...activeJobDetail, is_saved: !currentlySaved });
      }

      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      setErrorNotice(err instanceof Error ? err.message : 'Could not update bookmark.');
    }
  };

  // Score color helper
  const getScoreBadge = (score?: number | null) => {
    if (score === undefined || score === null) {
      return (
        <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full flex items-center space-x-1">
          <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
          <span>No Profile</span>
        </span>
      );
    }
    if (score >= 80) {
      return (
        <span className="text-xs font-bold text-emerald-800 bg-emerald-100/90 border border-emerald-300/80 px-2.5 py-1 rounded-full flex items-center space-x-1 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-emerald-700" />
          <span>{score.toFixed(0)}% • Strong Match</span>
        </span>
      );
    }
    if (score >= 60) {
      return (
        <span className="text-xs font-bold text-sky-800 bg-sky-100/90 border border-sky-300/80 px-2.5 py-1 rounded-full flex items-center space-x-1 shadow-sm">
          <TrendingUp className="w-3.5 h-3.5 text-sky-700" />
          <span>{score.toFixed(0)}% • Good Match</span>
        </span>
      );
    }
    if (score >= 40) {
      return (
        <span className="text-xs font-bold text-amber-800 bg-amber-100/90 border border-amber-300/80 px-2.5 py-1 rounded-full flex items-center space-x-1 shadow-sm">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
          <span>{score.toFixed(0)}% • Building Match</span>
        </span>
      );
    }
    return (
      <span className="text-xs font-medium text-slate-600 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full flex items-center space-x-1">
        <span>{score.toFixed(0)}% • Low Match</span>
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <Briefcase className="w-6 h-6 text-sky-600" />
            <span>Jobs & Opportunities</span>
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Browse curated industry roles with transparent, skill-based match evaluation.
          </p>
        </div>

        {isAuthenticated && (
          <button
            onClick={() => setSavedOnlyFilter(!savedOnlyFilter)}
            className={`inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition shadow-sm border ${
              savedOnlyFilter
                ? 'bg-amber-500 text-white border-amber-600 hover:bg-amber-600'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            <Bookmark className="w-4 h-4" />
            <span>{savedOnlyFilter ? 'Showing Saved Jobs' : 'Filter Saved Jobs'}</span>
          </button>
        )}
      </div>

      {/* Action Notification */}
      {actionNotice && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-2.5 rounded-lg text-xs flex items-center space-x-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span className="font-medium">{actionNotice}</span>
        </div>
      )}

      {/* Error Notice */}
      {errorNotice && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-2.5 rounded-lg text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span className="font-medium">{errorNotice}</span>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search title, company, skills..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition"
            />
          </div>

          {/* Location Filter */}
          <div className="relative">
            <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Location (e.g. Remote, City)..."
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition"
            />
          </div>

          {/* Employment Type */}
          <select
            value={employmentTypeFilter}
            onChange={(e) => setEmploymentTypeFilter(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs bg-white text-slate-700 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition"
          >
            <option value="">All Employment Types</option>
            <option value="full-time">Full-Time</option>
            <option value="part-time">Part-Time</option>
            <option value="contract">Contract</option>
          </select>

          {/* Experience Level */}
          <select
            value={experienceLevelFilter}
            onChange={(e) => setExperienceLevelFilter(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs bg-white text-slate-700 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition"
          >
            <option value="">All Experience Levels</option>
            <option value="entry">Entry Level</option>
            <option value="mid">Mid Level</option>
            <option value="senior">Senior Level</option>
          </select>
        </div>
      </div>

      {/* Main Split Layout: Job Cards Column + Detail/Match Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Job Cards List (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>Showing {jobs.length} of {totalJobs} jobs</span>
            {savedOnlyFilter && (
              <span className="font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
                Saved filter active
              </span>
            )}
          </div>

          {isLoadingJobs ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
              <Loader2 className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-2" />
              <p className="text-xs font-medium">Loading curated positions...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-10 text-center text-slate-500">
              <Briefcase className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-800">No jobs match your filters</p>
              <p className="text-xs text-slate-500 mt-1">Try resetting search keywords or location criteria.</p>
              <button
                onClick={() => {
                  setSearchTerm('');
                  setLocationFilter('');
                  setEmploymentTypeFilter('');
                  setExperienceLevelFilter('');
                  setSavedOnlyFilter(false);
                }}
                className="mt-4 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition"
              >
                Reset All Filters
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => {
                const isSelected = selectedJobId === job.id;
                return (
                  <div
                    key={job.id}
                    onClick={() => selectJob(job.id)}
                    className={`bg-white rounded-xl border p-4 cursor-pointer transition relative hover:shadow-md ${
                      isSelected
                        ? 'border-sky-500 ring-2 ring-sky-500/20 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-bold text-slate-900 truncate">
                          {job.title}
                        </h3>
                        <p className="text-xs font-semibold text-slate-600 mt-0.5">
                          {job.company}
                        </p>
                      </div>

                      {/* Bookmark Icon */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleSave(job.id, job.is_saved);
                        }}
                        title={job.is_saved ? 'Remove Bookmark' : 'Save Job'}
                        className={`p-1.5 rounded-lg transition ${
                          job.is_saved
                            ? 'text-amber-600 bg-amber-50 hover:bg-amber-100'
                            : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        {job.is_saved ? (
                          <BookmarkCheck className="w-4 h-4 fill-amber-500" />
                        ) : (
                          <Bookmark className="w-4 h-4" />
                        )}
                      </button>
                    </div>

                    {/* Metadata Badges */}
                    <div className="flex flex-wrap items-center gap-2 mt-2.5 text-[11px] text-slate-500">
                      <span className="flex items-center space-x-1">
                        <MapPin className="w-3 h-3 text-slate-400" />
                        <span>{job.location}</span>
                      </span>
                      <span>•</span>
                      <span className="capitalize">{job.employment_type}</span>
                      <span>•</span>
                      <span className="capitalize">{job.experience_level}</span>
                    </div>

                    {/* Skills previews */}
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {job.skills.slice(0, 4).map((sk) => (
                        <span
                          key={sk.id}
                          className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                            sk.is_required
                              ? 'bg-slate-100 text-slate-700 font-semibold'
                              : 'bg-slate-50 text-slate-500 border border-slate-200'
                          }`}
                        >
                          {sk.name}
                        </span>
                      ))}
                      {job.skills.length > 4 && (
                        <span className="text-[10px] text-slate-400 py-0.5">
                          +{job.skills.length - 4} more
                        </span>
                      )}
                    </div>

                    {/* Match Score Badge */}
                    <div className="mt-3.5 pt-2.5 border-t border-slate-100 flex items-center justify-between">
                      {getScoreBadge(job.match_score)}
                      <span className="text-[11px] text-sky-600 font-semibold flex items-center space-x-1 hover:underline">
                        <span>View Details</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                );
              })}

              {/* Pagination controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-600">
                  <button
                    disabled={currentPage <= 1}
                    onClick={() => loadJobs(currentPage - 1)}
                    className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg border border-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                    <span>Previous</span>
                  </button>
                  <span>Page {currentPage} of {totalPages}</span>
                  <button
                    disabled={currentPage >= totalPages}
                    onClick={() => loadJobs(currentPage + 1)}
                    className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg border border-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition"
                  >
                    <span>Next</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Selected Job Details & Match Breakdown (7 cols) */}
        <div className="lg:col-span-7 sticky top-4 space-y-4">
          {isLoadingDetail ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
              <Loader2 className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-2" />
              <p className="text-xs font-medium">Loading position specifications...</p>
            </div>
          ) : !activeJobDetail ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
              <Briefcase className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-slate-800">Select a Job</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Choose any job from the catalog on the left to review required skills, experience parameters, and deterministic match breakdown.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              {/* Job Header Card */}
              <div className="p-6 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-white">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                      {activeJobDetail.title}
                    </h2>
                    <p className="text-sm font-semibold text-sky-700 mt-0.5">
                      {activeJobDetail.company}
                    </p>
                    <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-slate-600">
                      <span className="flex items-center space-x-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{activeJobDetail.location}</span>
                      </span>
                      <span>•</span>
                      <span className="capitalize">{activeJobDetail.employment_type}</span>
                      <span>•</span>
                      <span className="capitalize">{activeJobDetail.experience_level}</span>
                      {activeJobDetail.salary_range && (
                        <>
                          <span>•</span>
                          <span className="font-semibold text-emerald-700 flex items-center space-x-0.5">
                            <DollarSign className="w-3.5 h-3.5" />
                            <span>{activeJobDetail.salary_range}</span>
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleToggleSave(activeJobDetail.id, activeJobDetail.is_saved)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition shadow-sm ${
                      activeJobDetail.is_saved
                        ? 'bg-amber-50 text-amber-800 border-amber-300 hover:bg-amber-100'
                        : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <Bookmark className={`w-3.5 h-3.5 ${activeJobDetail.is_saved ? 'fill-amber-500' : ''}`} />
                    <span>{activeJobDetail.is_saved ? 'Saved' : 'Save Job'}</span>
                  </button>
                </div>

                {/* Tabs Navigation */}
                <div className="flex space-x-2 mt-6 border-b border-slate-200 -mb-6 overflow-x-auto pb-1">
                  <button
                    type="button"
                    onClick={() => setDetailTab('match')}
                    className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center space-x-1.5 whitespace-nowrap ${
                      detailTab === 'match'
                        ? 'border-sky-600 text-sky-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Match</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDetailTab('gaps')}
                    className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center space-x-1.5 whitespace-nowrap ${
                      detailTab === 'gaps'
                        ? 'border-sky-600 text-sky-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>Skill Gaps</span>
                    {activeGaps && (activeGaps.missing_required_skills.length > 0 || activeGaps.experience_gap.experience_gap > 0) && (
                      <span className="ml-1 px-1.5 py-0.2 bg-rose-100 text-rose-700 rounded-full text-[10px] font-bold">
                        {activeGaps.missing_required_skills.length + (activeGaps.experience_gap.experience_gap > 0 ? 1 : 0)}
                      </span>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setDetailTab('simulator')}
                    className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center space-x-1.5 whitespace-nowrap ${
                      detailTab === 'simulator'
                        ? 'border-sky-600 text-sky-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    <Sliders className="w-3.5 h-3.5" />
                    <span>What-If</span>
                    {(simAddedSkills.length + simModifiedSkills.length + simRemovedSkills.length > 0 || (typeof simExperienceYears === 'number' && activeGaps && simExperienceYears !== activeGaps.experience_gap.candidate_experience_years)) && (
                      <span className="ml-1 w-2 h-2 rounded-full bg-amber-500"></span>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setDetailTab('roadmap')}
                    className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center space-x-1.5 whitespace-nowrap ${
                      detailTab === 'roadmap'
                        ? 'border-sky-600 text-sky-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    <Compass className="w-3.5 h-3.5" />
                    <span>Career Roadmap</span>
                    {activeRoadmap && (
                      <span
                        className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                          activeRoadmap.progress.progress_percentage === 100
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-indigo-100 text-indigo-700'
                        }`}
                      >
                        {activeRoadmap.progress.progress_percentage.toFixed(0)}%
                      </span>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setDetailTab('overview')}
                    className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center space-x-1.5 whitespace-nowrap ${
                      detailTab === 'overview'
                        ? 'border-sky-600 text-sky-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Job Details</span>
                  </button>
                </div>
              </div>

              {/* Tab Contents */}
              <div className="p-6">
                {detailTab === 'overview' && (
                  <div className="space-y-6 text-xs text-slate-700 leading-relaxed">
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                        Role Overview & Description
                      </h3>
                      <p className="whitespace-pre-line text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200">
                        {activeJobDetail.description}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                        <p className="font-semibold text-slate-900 flex items-center space-x-1.5">
                          <Clock className="w-4 h-4 text-sky-600" />
                          <span>Experience Requirement</span>
                        </p>
                        <p className="text-slate-600 mt-1 font-medium">
                          {activeJobDetail.min_experience_years > 0
                            ? `${activeJobDetail.min_experience_years} years minimum (${activeJobDetail.experience_level})`
                            : 'No minimum years required (Entry Level)'}
                        </p>
                      </div>

                      <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                        <p className="font-semibold text-slate-900 flex items-center space-x-1.5">
                          <GraduationCap className="w-4 h-4 text-sky-600" />
                          <span>Education Level</span>
                        </p>
                        <p className="text-slate-600 mt-1 font-medium">
                          {activeJobDetail.target_education_level} or equivalent
                        </p>
                      </div>
                    </div>

                    {/* Required Skills */}
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                        Required Technical Skills (Base Weight 0.50)
                      </h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {activeJobDetail.skills
                          .filter((s) => s.is_required)
                          .map((sk) => (
                            <div
                              key={sk.id}
                              className="p-2.5 rounded-lg border border-slate-200 bg-white flex items-center justify-between"
                            >
                              <span className="font-semibold text-slate-800">{sk.name}</span>
                              <span className="text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded capitalize">
                                {sk.min_proficiency}
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>

                    {/* Preferred Skills */}
                    {activeJobDetail.skills.some((s) => !s.is_required) && (
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                          Preferred / Nice-to-Have Skills (Base Weight 0.20)
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {activeJobDetail.skills
                            .filter((s) => !s.is_required)
                            .map((sk) => (
                              <div
                                key={sk.id}
                                className="p-2.5 rounded-lg border border-dashed border-slate-300 bg-slate-50 flex items-center justify-between"
                              >
                                <span className="text-slate-700">{sk.name}</span>
                                <span className="text-[10px] text-slate-500 capitalize">
                                  {sk.min_proficiency}
                                </span>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {detailTab === 'match' && (
                  <div>
                    {!isAuthenticated ? (
                      <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200">
                        <Briefcase className="w-10 h-10 text-sky-600 mx-auto mb-3" />
                        <h3 className="text-sm font-bold text-slate-900">Sign in for Match Analysis</h3>
                        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                          Sign in with your candidate account to see deterministic match scores, skill overlap, experience compatibility, and transferable related credits.
                        </p>
                        <button
                          onClick={() => navigate('/login')}
                          className="mt-4 px-4 py-2 bg-sky-600 text-white text-xs font-semibold rounded-lg hover:bg-sky-700 transition"
                        >
                          Sign In
                        </button>
                      </div>
                    ) : noProfileNotice ? (
                      <div className="p-8 text-center bg-sky-50/60 rounded-xl border border-sky-200">
                        <Award className="w-10 h-10 text-sky-600 mx-auto mb-3" />
                        <h3 className="text-sm font-bold text-slate-900">Career Profile Required</h3>
                        <p className="text-xs text-slate-600 mt-1 max-w-md mx-auto leading-relaxed">
                          Deterministic matching compares this role's requirements directly against your structured skills, verified education, and work experience. Please set up your profile or upload a resume to unlock instant match evaluation.
                        </p>
                        <div className="flex items-center justify-center space-x-3 mt-4">
                          <button
                            onClick={() => navigate('/resume')}
                            className="px-3.5 py-2 bg-sky-600 text-white text-xs font-semibold rounded-lg hover:bg-sky-700 transition"
                          >
                            Upload Resume
                          </button>
                          <button
                            onClick={() => navigate('/profile')}
                            className="px-3.5 py-2 bg-white text-slate-700 border border-slate-300 text-xs font-semibold rounded-lg hover:bg-slate-50 transition"
                          >
                            Edit Profile
                          </button>
                        </div>
                      </div>
                    ) : isLoadingMatch ? (
                      <div className="p-12 text-center text-slate-500">
                        <Loader2 className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-2" />
                        <p className="text-xs font-medium">Evaluating deterministic match algorithm...</p>
                      </div>
                    ) : !activeMatch ? (
                      <div className="p-8 text-center text-slate-500">
                        <p className="text-xs">No match evaluation available for this job posting.</p>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Overall Score Banner */}
                        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
                          <div>
                            <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">
                              Match Score
                            </span>
                            <div className="flex items-baseline space-x-3 mt-1">
                              <span className="text-4xl font-extrabold tracking-tight">
                                {activeMatch.overall_score.toFixed(1)}%
                              </span>
                              <span className="text-xs font-semibold text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-2 py-0.5 rounded">
                                {activeMatch.overall_score >= 80
                                  ? 'Strong Match'
                                  : activeMatch.overall_score >= 60
                                  ? 'Good Match'
                                  : activeMatch.overall_score >= 40
                                  ? 'Building Match'
                                  : 'Low Match'}
                              </span>
                            </div>
                            <p className="text-xs text-slate-300 mt-2 max-w-md leading-relaxed">
                              {activeMatch.explanation}
                            </p>
                          </div>

                          {/* Metric Ring / Summary stats */}
                          <div className="bg-slate-800/80 border border-slate-700 p-3.5 rounded-xl text-center min-w-[140px]">
                            <p className="text-[11px] text-slate-400">Skills Overlap</p>
                            <p className="text-lg font-bold text-white mt-0.5">
                              {activeMatch.matched_required_skills_count} / {activeMatch.total_required_skills_count}
                            </p>
                            <p className="text-[10px] text-slate-400 mt-0.5">Required Skills</p>
                          </div>
                        </div>

                        {/* Dimensional Breakdown Cards */}
                        <div>
                          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                            Match Breakdown
                          </h3>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {/* Required Skills */}
                            <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
                              <p className="text-[10px] font-semibold text-slate-500 uppercase">Required Skills</p>
                              <p className="text-lg font-bold text-slate-900 mt-0.5">
                                {activeMatch.required_skills_score.toFixed(0)}%
                              </p>
                              <p className="text-[10px] text-slate-400 mt-0.5">
                                Weight: {((activeMatch.active_weights['required_skills'] || 0.5) * 100).toFixed(0)}%
                              </p>
                            </div>

                            {/* Preferred Skills */}
                            <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
                              <p className="text-[10px] font-semibold text-slate-500 uppercase">Preferred Skills</p>
                              <p className="text-lg font-bold text-slate-900 mt-0.5">
                                {activeMatch.preferred_skills_score !== null
                                  ? `${activeMatch.preferred_skills_score.toFixed(0)}%`
                                  : 'N/A'}
                              </p>
                              <p className="text-[10px] text-slate-400 mt-0.5">
                                {activeMatch.preferred_skills_score !== null
                                  ? `Weight: ${((activeMatch.active_weights['preferred_skills'] || 0.2) * 100).toFixed(0)}%`
                                  : 'Weight redistributed'}
                              </p>
                            </div>

                            {/* Experience */}
                            <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
                              <p className="text-[10px] font-semibold text-slate-500 uppercase">Experience</p>
                              <p className="text-lg font-bold text-slate-900 mt-0.5">
                                {activeMatch.experience_score.toFixed(0)}%
                              </p>
                              <p className="text-[10px] text-slate-400 mt-0.5">
                                Weight: {((activeMatch.active_weights['experience'] || 0.2) * 100).toFixed(0)}%
                              </p>
                            </div>

                            {/* Education */}
                            <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
                              <p className="text-[10px] font-semibold text-slate-500 uppercase">Education</p>
                              <p className="text-lg font-bold text-slate-900 mt-0.5">
                                {activeMatch.education_score.toFixed(0)}%
                              </p>
                              <p className="text-[10px] text-slate-400 mt-0.5">
                                Weight: {((activeMatch.active_weights['education'] || 0.1) * 100).toFixed(0)}%
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Matched Skills Details */}
                        {activeMatch.matched_skills.length > 0 && (
                          <div>
                            <h4 className="text-xs font-bold text-emerald-800 flex items-center space-x-1.5 mb-2.5">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              <span>Why you match: Matched Skills ({activeMatch.matched_skills.length})</span>
                            </h4>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {activeMatch.matched_skills.map((sk, idx) => (
                                <div
                                  key={idx}
                                  className="p-2.5 rounded-lg border border-emerald-200 bg-emerald-50/50 flex items-center justify-between text-xs"
                                >
                                  <div>
                                    <span className="font-semibold text-slate-900">{sk.name}</span>
                                    <span className="ml-2 text-[10px] text-emerald-700 capitalize font-medium">
                                      {sk.candidate_proficiency}
                                    </span>
                                  </div>
                                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                                    {(sk.credit * 100).toFixed(0)}% Credit
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Partial / Transferable Related Skills */}
                        {activeMatch.partial_skills.length > 0 && (
                          <div>
                            <h4 className="text-xs font-bold text-sky-800 flex items-center space-x-1.5 mb-2.5">
                              <Sparkles className="w-4 h-4 text-sky-600" />
                              <span>Related Skills Credit ({activeMatch.partial_skills.length})</span>
                            </h4>
                            <div className="space-y-2">
                              {activeMatch.partial_skills.map((psk, idx) => (
                                <div
                                  key={idx}
                                  className="p-2.5 rounded-lg border border-sky-200 bg-sky-50/50 flex items-center justify-between text-xs"
                                >
                                  <div>
                                    <span className="font-semibold text-slate-800">{psk.candidate_skill_name}</span>
                                    <span className="text-slate-400 mx-1.5">→</span>
                                    <span className="font-semibold text-sky-800">{psk.job_skill_name}</span>
                                    <p className="text-[10px] text-slate-500 mt-0.5">
                                      Taxonomy relationship similarity: {(psk.similarity_weight * 100).toFixed(0)}%
                                    </p>
                                  </div>
                                  <span className="text-[10px] font-bold text-sky-800 bg-sky-100 px-2 py-0.5 rounded">
                                    {(psk.credit * 100).toFixed(0)}% Partial Credit
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Missing Required Skills */}
                        {activeMatch.missing_required_skills.length > 0 && (
                          <div>
                            <h4 className="text-xs font-bold text-rose-800 flex items-center space-x-1.5 mb-2.5">
                              <XCircle className="w-4 h-4 text-rose-600" />
                              <span>What is missing: Required Skills ({activeMatch.missing_required_skills.length})</span>
                            </h4>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {activeMatch.missing_required_skills.map((msk, idx) => (
                                <div
                                  key={idx}
                                  className="p-2.5 rounded-lg border border-rose-200 bg-rose-50/40 flex items-center justify-between text-xs"
                                >
                                  <span className="font-semibold text-slate-800">{msk.name}</span>
                                  <span className="text-[10px] text-rose-700 bg-rose-100 px-2 py-0.5 rounded capitalize">
                                    Needs {msk.required_proficiency}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Experience Gap Callout */}
                        <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3 text-xs">
                          <Clock className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="font-bold text-slate-900">Experience Compatibility</p>
                            <p className="text-slate-600 mt-0.5">{activeMatch.experience_gap_text}</p>
                          </div>
                        </div>

                        {/* Education Compatibility Callout */}
                        <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3 text-xs">
                          <GraduationCap className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="font-bold text-slate-900">Education Compatibility</p>
                            <p className="text-slate-600 mt-0.5">{activeMatch.education_compatibility.explanation}</p>
                          </div>
                        </div>

                        {/* Quick Nav to Skill Gaps, Simulator & Roadmap */}
                        <div className="pt-4 border-t border-slate-200 grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                          <button
                            type="button"
                            onClick={() => setDetailTab('gaps')}
                            className="py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition flex items-center justify-center space-x-1.5"
                          >
                            <TrendingUp className="w-3.5 h-3.5 text-sky-600" />
                            <span>Skill Gaps</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setDetailTab('simulator')}
                            className="py-2 px-3 bg-sky-50 hover:bg-sky-100 text-sky-800 font-semibold text-xs rounded-lg transition border border-sky-200 flex items-center justify-center space-x-1.5"
                          >
                            <Sliders className="w-3.5 h-3.5 text-sky-600" />
                            <span>What-If</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setDetailTab('roadmap')}
                            className="py-2 px-3 bg-indigo-50 hover:bg-indigo-100 text-indigo-800 font-semibold text-xs rounded-lg transition border border-indigo-200 flex items-center justify-center space-x-1.5"
                          >
                            <Compass className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Career Roadmap</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {detailTab === 'gaps' && (
                  <SkillGapAnalysis
                    gaps={activeGaps}
                    isLoading={isLoadingGaps}
                    error={gapsError}
                    onRetry={() => selectedJobId && selectJob(selectedJobId)}
                    onNavigateToResume={() => navigate('/resume')}
                    onNavigateToProfile={() => navigate('/profile')}
                    onSimulateAddSkill={handleQuickSimulateAddSkill}
                    onSwitchToSimulator={() => setDetailTab('simulator')}
                    onSwitchToRoadmap={() => setDetailTab('roadmap')}
                    isProfileRequired={noProfileNotice}
                  />
                )}

                {detailTab === 'simulator' && (
                  <CareerSimulator
                    jobTitle={activeJobDetail.title}
                    jobCompany={activeJobDetail.company}
                    missingSkills={
                      activeGaps?.missing_required_skills.map((s) => ({
                        name: s.name,
                        required_proficiency: s.required_proficiency,
                      })) || []
                    }
                    existingSkills={
                      activeGaps?.matched_required_skills
                        .concat(activeGaps?.matched_preferred_skills || [])
                        .map((s) => ({
                          name: s.name,
                          proficiency_level: s.candidate_proficiency,
                        })) ||
                      activeMatch?.matched_skills.map((s) => ({
                        name: s.name,
                        proficiency_level: s.candidate_proficiency,
                      })) ||
                      []
                    }
                    candidateExperienceYears={
                      activeGaps?.experience_gap.candidate_experience_years || 0
                    }
                    addedSkills={simAddedSkills}
                    modifiedSkills={simModifiedSkills}
                    removedSkills={simRemovedSkills}
                    simExperienceYears={simExperienceYears}
                    isSimulating={isSimulating}
                    simResult={simResult}
                    simError={simError}
                    isProfileRequired={noProfileNotice}
                    onAddSkill={handleAddSkill}
                    onRemoveAddedSkill={handleRemoveAddedSkill}
                    onModifySkill={handleModifySkill}
                    onRemoveModifiedSkill={handleRemoveModifiedSkill}
                    onToggleRemoveSkill={handleToggleRemoveSkill}
                    onChangeExperience={handleChangeExperience}
                    onRunSimulation={handleRunSimulation}
                    onResetScenario={handleResetScenario}
                    onNavigateToResume={() => navigate('/resume')}
                    onNavigateToProfile={() => navigate('/profile')}
                  />
                )}

                {detailTab === 'roadmap' && (
                  <div>
                    {!isAuthenticated ? (
                      <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200">
                        <Compass className="w-10 h-10 text-indigo-600 mx-auto mb-3" />
                        <h3 className="text-sm font-bold text-slate-900">Sign in for Career Roadmap</h3>
                        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                          Sign in with your candidate account to generate structured, prerequisite-aware milestones and track your skill acquisition progress toward this role.
                        </p>
                        <button
                          type="button"
                          onClick={() => navigate('/login')}
                          className="mt-4 px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition"
                        >
                          Sign In
                        </button>
                      </div>
                    ) : noProfileNotice ? (
                      <div className="p-8 text-center bg-amber-50/50 rounded-xl border border-amber-200">
                        <AlertCircle className="w-10 h-10 text-amber-600 mx-auto mb-3" />
                        <h3 className="text-sm font-bold text-amber-900">Career Profile Required</h3>
                        <p className="text-xs text-amber-700 mt-1 max-w-md mx-auto">
                          To generate a personalized roadmap, we need your current skills and experience. Please create your profile or upload a resume first.
                        </p>
                        <div className="mt-4 flex items-center justify-center space-x-3">
                          <button
                            type="button"
                            onClick={() => navigate('/resume')}
                            className="px-4 py-2 bg-amber-600 text-white text-xs font-semibold rounded-lg hover:bg-amber-700 transition"
                          >
                            Upload Resume
                          </button>
                          <button
                            type="button"
                            onClick={() => navigate('/profile')}
                            className="px-4 py-2 bg-white border border-amber-300 text-amber-800 text-xs font-semibold rounded-lg hover:bg-amber-50 transition"
                          >
                            Complete Profile
                          </button>
                        </div>
                      </div>
                    ) : isLoadingRoadmap ? (
                      <div className="py-16 text-center">
                        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
                        <p className="text-xs font-medium text-slate-600">Loading your career roadmap...</p>
                      </div>
                    ) : isGeneratingRoadmap ? (
                      <div className="py-16 text-center">
                        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
                        <p className="text-sm font-semibold text-slate-900">Generating Personalized Roadmap...</p>
                        <p className="text-xs text-slate-500 mt-1">Analyzing skill gaps, ordering prerequisites, and tailoring milestones.</p>
                      </div>
                    ) : activeRoadmap ? (
                      <CareerRoadmap
                        roadmap={activeRoadmap}
                        jobTitle={activeJobDetail.title}
                        company={activeJobDetail.company}
                        isRegenerating={isGeneratingRoadmap}
                        onRegenerate={handleGenerateRoadmap}
                        onStatusChange={handleRoadmapStatusChange}
                        updatingItemId={updatingItemId}
                      />
                    ) : (
                      <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200">
                        <Compass className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
                        <h3 className="text-base font-bold text-slate-900">No Roadmap Generated Yet</h3>
                        <p className="text-xs text-slate-500 mt-1 max-w-lg mx-auto">
                          Transform your identified skill gaps for <span className="font-semibold text-slate-700">{activeJobDetail.title}</span> at <span className="font-semibold text-slate-700">{activeJobDetail.company}</span> into a step-by-step, 4-stage action plan with prerequisites, estimated hours, and project deliverables.
                        </p>
                        {roadmapError && (
                          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs max-w-md mx-auto">
                            {roadmapError}
                          </div>
                        )}
                        <div className="mt-6 flex items-center justify-center space-x-3">
                          <button
                            type="button"
                            onClick={handleGenerateRoadmap}
                            disabled={isGeneratingRoadmap}
                            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
                          >
                            <Sparkles className="w-4 h-4" />
                            <span>Generate Career Roadmap</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
