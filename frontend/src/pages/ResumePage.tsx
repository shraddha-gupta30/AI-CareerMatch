import React, { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigationStore } from '../store/navigationStore';
import {
  uploadResume,
  listResumes,
  getResumeDetail,
  deleteResume,
  applyResumeDraft,
} from '../services/resumes';
import {
  ResumeResponse,
  ResumeDetailResponse,
  StructuredResumeData,
  ExtractedSkillItem,
  ExtractedExperienceItem,
  ExtractedEducationItem,
  ExtractedProjectItem,
  ExtractedCertificationItem,
} from '../types/resume';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Trash2,
  ArrowRight,
  Sparkles,
  Loader2,
  Briefcase,
  GraduationCap,
  FolderGit2,
  Award,
  Plus,
  Layers,
} from 'lucide-react';

const PROFICIENCY_OPTIONS = ['beginner', 'intermediate', 'advanced', 'expert'];

export const ResumePage: React.FC = () => {
  const { token } = useAuthStore();
  const { navigate } = useNavigationStore();

  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [activeResumeDetail, setActiveResumeDetail] = useState<ResumeDetailResponse | null>(null);
  const [stagingDraft, setStagingDraft] = useState<StructuredResumeData | null>(null);

  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  const [uploadError, setUploadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Active section tab in staging review
  const [activeTab, setActiveTab] = useState<'profile' | 'skills' | 'experience' | 'education' | 'projects' | 'certifications'>('skills');

  // Load resumes list
  const loadResumes = async () => {
    if (!token) return;
    setIsLoadingList(true);
    setActionError(null);
    try {
      const data = await listResumes(token);
      setResumes(data);
      if (data.length > 0 && !selectedResumeId) {
        // Automatically select the most recent resume
        selectResume(data[0].id);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to load resumes list.');
    } finally {
      setIsLoadingList(false);
    }
  };

  useEffect(() => {
    loadResumes();
  }, [token]);

  // Select a specific resume to review
  const selectResume = async (id: string) => {
    if (!token) return;
    setSelectedResumeId(id);
    setIsLoadingDetail(true);
    setActionError(null);
    setSuccessNotice(null);
    try {
      const detail = await getResumeDetail(id, token);
      setActiveResumeDetail(detail);
      if (detail.parsed_staging_json) {
        setStagingDraft(JSON.parse(JSON.stringify(detail.parsed_staging_json)));
      } else {
        setStagingDraft(null);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to load resume details.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // File upload handler
  const handleFileUpload = async (file: File) => {
    if (!token) return;
    setUploadError(null);
    setSuccessNotice(null);

    // Client-side validations
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setUploadError('Only PDF files are supported. Please select a valid .pdf document.');
      return;
    }

    const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
    if (file.size > MAX_SIZE) {
      setUploadError('File size exceeds the 10 MB limit. Please select a smaller resume file.');
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadResume(file, token);
      await loadResumes();
      setSelectedResumeId(result.id);
      setActiveResumeDetail(result);
      if (result.parsed_staging_json) {
        setStagingDraft(JSON.parse(JSON.stringify(result.parsed_staging_json)));
        setSuccessNotice('Resume parsed and structured staging draft generated! Review below before applying to your profile.');
      } else if (result.status === 'failed') {
        setUploadError(result.error_message || 'Resume parsing could not be completed.');
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to upload and process resume.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Drag & drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // Delete resume
  const handleDeleteResume = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!token) return;
    if (!confirm('Are you sure you want to delete this resume? This will also remove its uploaded PDF file and draft.')) {
      return;
    }

    try {
      await deleteResume(id, token);
      if (selectedResumeId === id) {
        setSelectedResumeId(null);
        setActiveResumeDetail(null);
        setStagingDraft(null);
      }
      await loadResumes();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to delete resume.');
    }
  };

  // Apply staging draft to candidate profile
  const handleApplyToProfile = async () => {
    if (!token || !selectedResumeId || !stagingDraft) return;
    setIsApplying(true);
    setActionError(null);
    setSuccessNotice(null);

    try {
      const result = await applyResumeDraft(selectedResumeId, stagingDraft, token);
      setSuccessNotice(
        `Successfully applied resume to profile! Updated ${result.skills_applied} skills, ${result.experience_records} experience records, ${result.education_records} education records, and ${result.project_records} projects.`
      );
      if (activeResumeDetail) {
        setActiveResumeDetail({ ...activeResumeDetail, status: 'applied' });
      }
      await loadResumes();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to apply resume to profile.');
    } finally {
      setIsApplying(false);
    }
  };

  // Staging Draft Field Updaters
  const updateSkill = (index: number, updates: Partial<ExtractedSkillItem>) => {
    if (!stagingDraft) return;
    const updatedSkills = [...stagingDraft.skills];
    updatedSkills[index] = { ...updatedSkills[index], ...updates };
    setStagingDraft({ ...stagingDraft, skills: updatedSkills });
  };

  const removeSkill = (index: number) => {
    if (!stagingDraft) return;
    const updatedSkills = stagingDraft.skills.filter((_, i) => i !== index);
    setStagingDraft({ ...stagingDraft, skills: updatedSkills });
  };

  const addCustomSkill = () => {
    if (!stagingDraft) return;
    const newSkill: ExtractedSkillItem = {
      name: 'New Skill',
      proficiency_level: 'intermediate',
      years_experience: 1.0,
      matched: false,
      proficiency_source: 'user_verified',
      is_verified: true,
    };
    setStagingDraft({ ...stagingDraft, skills: [newSkill, ...stagingDraft.skills] });
  };

  const updateExperience = (index: number, updates: Partial<ExtractedExperienceItem>) => {
    if (!stagingDraft) return;
    const list = [...stagingDraft.experience];
    list[index] = { ...list[index], ...updates };
    setStagingDraft({ ...stagingDraft, experience: list });
  };

  const removeExperience = (index: number) => {
    if (!stagingDraft) return;
    const list = stagingDraft.experience.filter((_, i) => i !== index);
    setStagingDraft({ ...stagingDraft, experience: list });
  };

  const addExperience = () => {
    if (!stagingDraft) return;
    const item: ExtractedExperienceItem = {
      company: 'Company Name',
      title: 'Role Title',
      location: 'Remote',
      start_date: '2023-01',
      end_date: null,
      is_current: true,
      description: 'Key accomplishments and responsibilities...',
      technologies: [],
    };
    setStagingDraft({ ...stagingDraft, experience: [item, ...stagingDraft.experience] });
  };

  const updateEducation = (index: number, updates: Partial<ExtractedEducationItem>) => {
    if (!stagingDraft) return;
    const list = [...stagingDraft.education];
    list[index] = { ...list[index], ...updates };
    setStagingDraft({ ...stagingDraft, education: list });
  };

  const removeEducation = (index: number) => {
    if (!stagingDraft) return;
    const list = stagingDraft.education.filter((_, i) => i !== index);
    setStagingDraft({ ...stagingDraft, education: list });
  };

  const addEducation = () => {
    if (!stagingDraft) return;
    const item: ExtractedEducationItem = {
      institution: 'University or College',
      degree: 'Bachelor of Science',
      field_of_study: 'Computer Science',
      start_date: '2019',
      end_date: '2023',
    };
    setStagingDraft({ ...stagingDraft, education: [item, ...stagingDraft.education] });
  };

  const updateProject = (index: number, updates: Partial<ExtractedProjectItem>) => {
    if (!stagingDraft) return;
    const list = [...stagingDraft.projects];
    list[index] = { ...list[index], ...updates };
    setStagingDraft({ ...stagingDraft, projects: list });
  };

  const removeProject = (index: number) => {
    if (!stagingDraft) return;
    const list = stagingDraft.projects.filter((_, i) => i !== index);
    setStagingDraft({ ...stagingDraft, projects: list });
  };

  const addProject = () => {
    if (!stagingDraft) return;
    const item: ExtractedProjectItem = {
      title: 'Project Name',
      description: 'Project description and technical achievements...',
      technologies: [],
    };
    setStagingDraft({ ...stagingDraft, projects: [item, ...stagingDraft.projects] });
  };

  const updateCertification = (index: number, updates: Partial<ExtractedCertificationItem>) => {
    if (!stagingDraft) return;
    const list = [...stagingDraft.certifications];
    list[index] = { ...list[index], ...updates };
    setStagingDraft({ ...stagingDraft, certifications: list });
  };

  const removeCertification = (index: number) => {
    if (!stagingDraft) return;
    const list = stagingDraft.certifications.filter((_, i) => i !== index);
    setStagingDraft({ ...stagingDraft, certifications: list });
  };

  const addCertification = () => {
    if (!stagingDraft) return;
    const item: ExtractedCertificationItem = {
      name: 'Certification Name',
      issuing_organization: 'Issuing Organization',
      issue_date: '2023',
    };
    setStagingDraft({ ...stagingDraft, certifications: [item, ...stagingDraft.certifications] });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-sky-600 bg-sky-50 px-3 py-1 rounded-full text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Phase 4 • AI Resume Extraction & Taxonomy Matcher</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Resume Upload & Staging Review
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Upload your PDF resume to extract structured skills, work history, and education. Review and confirm changes before applying them to your Career Profile.
          </p>
        </div>
      </div>

      {/* Global Alerts */}
      {successNotice && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl p-4 flex items-start space-x-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1 text-sm font-medium">
            <p>{successNotice}</p>
            <div className="mt-2">
              <button
                onClick={() => navigate('/profile')}
                className="inline-flex items-center text-xs font-semibold text-emerald-700 hover:text-emerald-900 underline"
              >
                Go to Career Profile <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </button>
            </div>
          </div>
        </div>
      )}

      {actionError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm font-medium flex-1">{actionError}</p>
        </div>
      )}

      {/* Main Grid: Upload + History / Selected Review */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Upload Zone + Uploaded Resumes */}
        <div className="lg:col-span-1 space-y-6">
          {/* Upload Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-3 flex items-center space-x-2">
              <UploadCloud className="w-4 h-4 text-sky-600" />
              <span>Upload Resume PDF</span>
            </h2>

            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
                dragActive
                  ? 'border-sky-500 bg-sky-50/50'
                  : 'border-slate-300 hover:border-sky-400 bg-slate-50/50 hover:bg-slate-50'
              } ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />

              {isUploading ? (
                <div className="flex flex-col items-center justify-center space-y-3 py-3">
                  <Loader2 className="w-8 h-8 text-sky-600 animate-spin" />
                  <p className="text-xs font-semibold text-slate-700">Extracting & Normalizing Skills...</p>
                  <p className="text-[11px] text-slate-500">Running pure-Python PDF reader and AI extraction</p>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center space-y-2 py-2">
                  <div className="w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center text-sky-600">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-semibold text-slate-700">
                    Click to browse or drop PDF here
                  </p>
                  <p className="text-[11px] text-slate-500">Max size 10 MB • Text-based PDF</p>
                </div>
              )}
            </div>

            {uploadError && (
              <div className="mt-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg p-3 text-xs flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold">Upload Notice</p>
                  <p className="mt-0.5">{uploadError}</p>
                </div>
              </div>
            )}
          </div>

          {/* Resumes List Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                <FileText className="w-4 h-4 text-slate-600" />
                <span>Uploaded Resumes</span>
              </h2>
              <span className="text-xs text-slate-500 font-mono">({resumes.length})</span>
            </div>

            {isLoadingList ? (
              <div className="py-8 flex justify-center">
                <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
              </div>
            ) : resumes.length === 0 ? (
              <div className="text-center py-6 text-slate-500">
                <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                <p className="text-xs">No resumes uploaded yet.</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Upload a PDF to start staging review.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {resumes.map((res) => {
                  const isSelected = selectedResumeId === res.id;
                  let statusBadge = (
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-amber-100 text-amber-800">
                      Pending Review
                    </span>
                  );
                  if (res.status === 'applied') {
                    statusBadge = (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-emerald-100 text-emerald-800">
                        Applied
                      </span>
                    );
                  } else if (res.status === 'failed') {
                    statusBadge = (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-rose-100 text-rose-800">
                        Failed
                      </span>
                    );
                  } else if (res.status === 'processing') {
                    statusBadge = (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-sky-100 text-sky-800">
                        Processing
                      </span>
                    );
                  }

                  return (
                    <div
                      key={res.id}
                      onClick={() => selectResume(res.id)}
                      className={`p-3 rounded-lg border text-left transition cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'border-sky-500 bg-sky-50/60 shadow-xs'
                          : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="min-w-0 flex-1 mr-2">
                        <p className="text-xs font-semibold text-slate-900 truncate">
                          {res.file_name}
                        </p>
                        <div className="flex items-center space-x-2 mt-1">
                          {statusBadge}
                          <span className="text-[10px] text-slate-400 font-mono">
                            {(res.file_size_bytes / 1024).toFixed(0)} KB
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDeleteResume(res.id, e)}
                        title="Delete resume"
                        className="text-slate-400 hover:text-rose-600 p-1 rounded hover:bg-rose-50 transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Staging Review Editor */}
        <div className="lg:col-span-2 space-y-6">
          {isLoadingDetail ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 flex flex-col items-center justify-center space-y-3">
              <Loader2 className="w-8 h-8 text-sky-600 animate-spin" />
              <p className="text-xs text-slate-600 font-medium">Loading staging review draft...</p>
            </div>
          ) : !activeResumeDetail ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
              <Layers className="w-12 h-12 mx-auto text-slate-300 mb-3" />
              <h3 className="text-sm font-semibold text-slate-800">No Resume Selected</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Upload a resume or select one from the left to inspect extracted skills, experience, and education.
              </p>
            </div>
          ) : activeResumeDetail.status === 'failed' ? (
            <div className="bg-white rounded-xl border border-rose-200 p-8">
              <div className="flex items-start space-x-3 text-rose-700">
                <AlertCircle className="w-6 h-6 flex-shrink-0 mt-0.5 text-rose-600" />
                <div className="space-y-2">
                  <h3 className="text-sm font-bold">Extraction Processing Note</h3>
                  <p className="text-xs text-rose-800 font-medium">
                    {activeResumeDetail.error_message || 'Resume text extraction encountered an error.'}
                  </p>
                  <p className="text-xs text-slate-600 mt-2">
                    If this is due to an unconfigured Gemini API key, ensure <code>GEMINI_API_KEY</code> is set in your <code>backend/.env</code> file, then upload again.
                  </p>
                </div>
              </div>
            </div>
          ) : !stagingDraft ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
              <p className="text-xs">No structured staging draft available for this resume.</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              {/* Card Header & Tabs */}
              <div className="border-b border-slate-200 bg-slate-50/70 p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                  <div>
                    <h2 className="text-base font-semibold text-slate-900">
                      Staging Review & Normalization
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Verify and adjust extracted candidate attributes before applying to your live Career Profile.
                    </p>
                  </div>

                  <button
                    onClick={handleApplyToProfile}
                    disabled={isApplying}
                    className="inline-flex items-center justify-center px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold shadow-xs transition disabled:opacity-50"
                  >
                    {isApplying ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                        Applying to Profile...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                        Confirm & Apply to Profile
                      </>
                    )}
                  </button>
                </div>

                {/* Tabs */}
                <div className="flex space-x-1 overflow-x-auto text-xs font-medium border-b border-slate-200 pb-1">
                  {[
                    { id: 'skills', label: `Skills (${stagingDraft.skills.length})`, icon: Sparkles },
                    { id: 'profile', label: 'Profile Summary', icon: Briefcase },
                    { id: 'experience', label: `Experience (${stagingDraft.experience.length})`, icon: Briefcase },
                    { id: 'education', label: `Education (${stagingDraft.education.length})`, icon: GraduationCap },
                    { id: 'projects', label: `Projects (${stagingDraft.projects.length})`, icon: FolderGit2 },
                    { id: 'certifications', label: `Certifications (${stagingDraft.certifications.length})`, icon: Award },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap transition ${
                          isActive
                            ? 'bg-sky-600 text-white font-semibold shadow-xs'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{tab.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Tab Contents */}
              <div className="p-5">
                {/* 1. SKILLS TAB */}
                {activeTab === 'skills' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide">
                          Taxonomy Mapped Skills ({stagingDraft.skills.length})
                        </h3>
                        <p className="text-[11px] text-slate-500">
                          Green badges denote exact or alias matches to master skill taxonomy.
                        </p>
                      </div>
                      <button
                        onClick={addCustomSkill}
                        className="inline-flex items-center text-xs font-medium text-sky-600 hover:text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md transition"
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" /> Add Skill
                      </button>
                    </div>

                    <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
                      {stagingDraft.skills.map((skill, index) => (
                        <div
                          key={index}
                          className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                        >
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center space-x-2">
                              <input
                                type="text"
                                value={skill.name}
                                onChange={(e) => updateSkill(index, { name: e.target.value })}
                                className="font-semibold text-slate-800 bg-white px-2 py-0.5 border border-slate-200 rounded text-xs focus:ring-1 focus:ring-sky-500 outline-hidden"
                              />

                              {skill.matched ? (
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold flex items-center space-x-1">
                                  <span>Matched: {skill.canonical_name || skill.name}</span>
                                  {skill.category && <span className="opacity-75">({skill.category})</span>}
                                </span>
                              ) : (
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                                  Custom (Unmatched)
                                </span>
                              )}
                            </div>
                            <div className="flex items-center space-x-2 text-[11px] text-slate-500">
                              <span>Source: {skill.proficiency_source}</span>
                            </div>
                          </div>

                          <div className="flex items-center space-x-3">
                            <div>
                              <label className="text-[10px] uppercase text-slate-400 font-semibold block">Proficiency</label>
                              <select
                                value={skill.proficiency_level}
                                onChange={(e) => updateSkill(index, { proficiency_level: e.target.value })}
                                className="bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-700 focus:ring-1 focus:ring-sky-500 outline-hidden"
                              >
                                {PROFICIENCY_OPTIONS.map((opt) => (
                                  <option key={opt} value={opt}>
                                    {opt.charAt(0).toUpperCase() + opt.slice(1)}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div>
                              <label className="text-[10px] uppercase text-slate-400 font-semibold block">Years</label>
                              <input
                                type="number"
                                step="0.5"
                                min="0"
                                max="50"
                                value={skill.years_experience}
                                onChange={(e) => updateSkill(index, { years_experience: parseFloat(e.target.value) || 0.0 })}
                                className="w-16 bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-700 text-right focus:ring-1 focus:ring-sky-500 outline-hidden"
                              />
                            </div>

                            <button
                              onClick={() => removeSkill(index)}
                              title="Remove skill"
                              className="text-slate-400 hover:text-rose-600 p-1.5 rounded hover:bg-rose-50 transition"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 2. PROFILE SUMMARY TAB */}
                {activeTab === 'profile' && (
                  <div className="space-y-4 text-xs">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Extracted Full Name</label>
                        <input
                          type="text"
                          value={stagingDraft.full_name || ''}
                          onChange={(e) => setStagingDraft({ ...stagingDraft, full_name: e.target.value })}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 focus:ring-1 focus:ring-sky-500 outline-hidden"
                        />
                      </div>

                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Target / Inferred Role</label>
                        <input
                          type="text"
                          value={stagingDraft.target_role || ''}
                          onChange={(e) => setStagingDraft({ ...stagingDraft, target_role: e.target.value })}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 focus:ring-1 focus:ring-sky-500 outline-hidden"
                        />
                      </div>

                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Professional Headline</label>
                        <input
                          type="text"
                          value={stagingDraft.headline || ''}
                          onChange={(e) => setStagingDraft({ ...stagingDraft, headline: e.target.value })}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 focus:ring-1 focus:ring-sky-500 outline-hidden"
                        />
                      </div>

                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Total Experience (Years)</label>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          value={stagingDraft.total_experience_years}
                          onChange={(e) =>
                            setStagingDraft({ ...stagingDraft, total_experience_years: parseFloat(e.target.value) || 0.0 })
                          }
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 focus:ring-1 focus:ring-sky-500 outline-hidden"
                        />
                      </div>

                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Target Location</label>
                        <input
                          type="text"
                          value={stagingDraft.target_location || ''}
                          onChange={(e) => setStagingDraft({ ...stagingDraft, target_location: e.target.value })}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 focus:ring-1 focus:ring-sky-500 outline-hidden"
                        />
                      </div>

                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Target Employment Type</label>
                        <input
                          type="text"
                          value={stagingDraft.target_employment_type || 'Full-time'}
                          onChange={(e) => setStagingDraft({ ...stagingDraft, target_employment_type: e.target.value })}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 focus:ring-1 focus:ring-sky-500 outline-hidden"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="font-semibold text-slate-700 block mb-1">Professional Bio / Summary</label>
                      <textarea
                        rows={4}
                        value={stagingDraft.bio || ''}
                        onChange={(e) => setStagingDraft({ ...stagingDraft, bio: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 focus:ring-1 focus:ring-sky-500 outline-hidden leading-relaxed"
                      />
                    </div>
                  </div>
                )}

                {/* 3. EXPERIENCE TAB */}
                {activeTab === 'experience' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide">
                        Work Experience ({stagingDraft.experience.length})
                      </h3>
                      <button
                        onClick={addExperience}
                        className="inline-flex items-center text-xs font-medium text-sky-600 hover:text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md transition"
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" /> Add Position
                      </button>
                    </div>

                    <div className="space-y-4 max-h-[480px] overflow-y-auto pr-1">
                      {stagingDraft.experience.map((exp, index) => (
                        <div key={index} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3 text-xs">
                          <div className="flex items-center justify-between">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 flex-1 mr-3">
                              <input
                                type="text"
                                placeholder="Company"
                                value={exp.company}
                                onChange={(e) => updateExperience(index, { company: e.target.value })}
                                className="font-semibold bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-900"
                              />
                              <input
                                type="text"
                                placeholder="Role Title"
                                value={exp.title}
                                onChange={(e) => updateExperience(index, { title: e.target.value })}
                                className="bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-900"
                              />
                            </div>
                            <button
                              onClick={() => removeExperience(index)}
                              className="text-slate-400 hover:text-rose-600 p-1"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            <input
                              type="text"
                              placeholder="Start (YYYY-MM)"
                              value={exp.start_date}
                              onChange={(e) => updateExperience(index, { start_date: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                            <input
                              type="text"
                              placeholder="End (YYYY-MM)"
                              value={exp.end_date || ''}
                              disabled={exp.is_current}
                              onChange={(e) => updateExperience(index, { end_date: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700 disabled:bg-slate-100"
                            />
                            <div className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                checked={exp.is_current}
                                onChange={(e) => updateExperience(index, { is_current: e.target.checked })}
                                className="rounded text-sky-600"
                              />
                              <span className="text-slate-600">Current Role</span>
                            </div>
                            <input
                              type="text"
                              placeholder="Location"
                              value={exp.location || ''}
                              onChange={(e) => updateExperience(index, { location: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                          </div>

                          <textarea
                            rows={3}
                            placeholder="Description of duties and accomplishments..."
                            value={exp.description || ''}
                            onChange={(e) => updateExperience(index, { description: e.target.value })}
                            className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-slate-700 leading-relaxed"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 4. EDUCATION TAB */}
                {activeTab === 'education' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide">
                        Education & Academics ({stagingDraft.education.length})
                      </h3>
                      <button
                        onClick={addEducation}
                        className="inline-flex items-center text-xs font-medium text-sky-600 hover:text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md transition"
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" /> Add Education
                      </button>
                    </div>

                    <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                      {stagingDraft.education.map((edu, index) => (
                        <div key={index} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <input
                              type="text"
                              placeholder="Institution"
                              value={edu.institution}
                              onChange={(e) => updateEducation(index, { institution: e.target.value })}
                              className="font-semibold bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-900 flex-1 mr-3"
                            />
                            <button
                              onClick={() => removeEducation(index)}
                              className="text-slate-400 hover:text-rose-600 p-1"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <input
                              type="text"
                              placeholder="Degree"
                              value={edu.degree}
                              onChange={(e) => updateEducation(index, { degree: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-700"
                            />
                            <input
                              type="text"
                              placeholder="Field of Study"
                              value={edu.field_of_study}
                              onChange={(e) => updateEducation(index, { field_of_study: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-700"
                            />
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <input
                              type="text"
                              placeholder="Start Date"
                              value={edu.start_date || ''}
                              onChange={(e) => updateEducation(index, { start_date: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                            <input
                              type="text"
                              placeholder="End Date"
                              value={edu.end_date || ''}
                              onChange={(e) => updateEducation(index, { end_date: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                            <input
                              type="text"
                              placeholder="Grade / GPA / Honors"
                              value={edu.grade_gpa || ''}
                              onChange={(e) => updateEducation(index, { grade_gpa: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 5. PROJECTS TAB */}
                {activeTab === 'projects' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide">
                        Projects ({stagingDraft.projects.length})
                      </h3>
                      <button
                        onClick={addProject}
                        className="inline-flex items-center text-xs font-medium text-sky-600 hover:text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md transition"
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" /> Add Project
                      </button>
                    </div>

                    <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                      {stagingDraft.projects.map((proj, index) => (
                        <div key={index} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <input
                              type="text"
                              placeholder="Project Title"
                              value={proj.title}
                              onChange={(e) => updateProject(index, { title: e.target.value })}
                              className="font-semibold bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-900 flex-1 mr-3"
                            />
                            <button
                              onClick={() => removeProject(index)}
                              className="text-slate-400 hover:text-rose-600 p-1"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>

                          <textarea
                            rows={2}
                            placeholder="Description..."
                            value={proj.description}
                            onChange={(e) => updateProject(index, { description: e.target.value })}
                            className="w-full bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-700 leading-relaxed"
                          />

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <input
                              type="text"
                              placeholder="Repository URL"
                              value={proj.repository_url || ''}
                              onChange={(e) => updateProject(index, { repository_url: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                            <input
                              type="text"
                              placeholder="Live Demo URL"
                              value={proj.live_url || ''}
                              onChange={(e) => updateProject(index, { live_url: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 6. CERTIFICATIONS TAB */}
                {activeTab === 'certifications' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide">
                        Certifications & Credentials ({stagingDraft.certifications.length})
                      </h3>
                      <button
                        onClick={addCertification}
                        className="inline-flex items-center text-xs font-medium text-sky-600 hover:text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md transition"
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" /> Add Certification
                      </button>
                    </div>

                    <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                      {stagingDraft.certifications.map((cert, index) => (
                        <div key={index} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <input
                              type="text"
                              placeholder="Certification Name"
                              value={cert.name}
                              onChange={(e) => updateCertification(index, { name: e.target.value })}
                              className="font-semibold bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-900 flex-1 mr-3"
                            />
                            <button
                              onClick={() => removeCertification(index)}
                              className="text-slate-400 hover:text-rose-600 p-1"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                            <input
                              type="text"
                              placeholder="Issuing Organization"
                              value={cert.issuing_organization}
                              onChange={(e) => updateCertification(index, { issuing_organization: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2.5 py-1 text-slate-700"
                            />
                            <input
                              type="text"
                              placeholder="Issue Date"
                              value={cert.issue_date || ''}
                              onChange={(e) => updateCertification(index, { issue_date: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                            <input
                              type="text"
                              placeholder="Credential ID"
                              value={cert.credential_id || ''}
                              onChange={(e) => updateCertification(index, { credential_id: e.target.value })}
                              className="bg-white border border-slate-200 rounded px-2 py-1 text-slate-700"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
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
