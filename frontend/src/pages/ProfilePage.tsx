import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { fetchProfile, saveProfile } from '../services/profile';
import { CandidateProfile, ProfilePayload } from '../types/profile';
import {
  Briefcase,
  MapPin,
  Clock,
  Edit3,
  Save,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Calendar,
} from 'lucide-react';

const EMPLOYMENT_TYPES = [
  'Full-time',
  'Part-time',
  'Contract',
  'Internship',
];

export const ProfilePage: React.FC = () => {
  const { user, token } = useAuthStore();

  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Form State
  const [targetRole, setTargetRole] = useState('');
  const [headline, setHeadline] = useState('');
  const [bio, setBio] = useState('');
  const [targetLocation, setTargetLocation] = useState('');
  const [targetEmploymentType, setTargetEmploymentType] = useState('Full-time');
  const [experienceYears, setExperienceYears] = useState('0.0');

  const loadProfile = async () => {
    if (!token) return;
    setIsLoading(true);
    setApiError(null);
    try {
      const data = await fetchProfile(token);
      setProfile(data);
      if (data) {
        setTargetRole(data.target_role || '');
        setHeadline(data.headline || '');
        setBio(data.bio || '');
        setTargetLocation(data.target_location || '');
        setTargetEmploymentType(data.target_employment_type || 'Full-time');
        setExperienceYears(String(data.total_experience_years || 0.0));
      } else {
        // Empty profile state: open editor automatically
        setIsEditing(true);
      }
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Failed to load career profile.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [token]);

  const handleCancel = () => {
    setValidationError(null);
    setSuccessMessage(null);
    if (profile) {
      setTargetRole(profile.target_role || '');
      setHeadline(profile.headline || '');
      setBio(profile.bio || '');
      setTargetLocation(profile.target_location || '');
      setTargetEmploymentType(profile.target_employment_type || 'Full-time');
      setExperienceYears(String(profile.total_experience_years || 0.0));
      setIsEditing(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setSuccessMessage(null);
    setApiError(null);

    const trimmedRole = targetRole.trim();
    if (trimmedRole.length < 2) {
      setValidationError('Target role must be at least 2 characters long.');
      return;
    }

    const expNum = parseFloat(experienceYears);
    if (isNaN(expNum) || expNum < 0) {
      setValidationError('Years of experience must be a non-negative number (e.g. 2.5).');
      return;
    }

    if (expNum > 60) {
      setValidationError('Years of experience must be realistic (maximum 60 years).');
      return;
    }

    if (!token) {
      setApiError('Session expired. Please log in again.');
      return;
    }

    setIsSaving(true);
    try {
      const payload: ProfilePayload = {
        target_role: trimmedRole,
        headline: headline.trim() || null,
        bio: bio.trim() || null,
        target_location: targetLocation.trim() || null,
        target_employment_type: targetEmploymentType,
        total_experience_years: expNum,
      };

      const updated = await saveProfile(payload, token);
      setProfile(updated);
      setIsEditing(false);
      setSuccessMessage('Career profile saved successfully.');
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Career Profile
          </h1>
          <p className="text-xs text-slate-600 mt-1">
            Manage your career aspirations, professional background, and matching preferences.
          </p>
        </div>

        {!isLoading && !isEditing && (
          <button
            onClick={() => {
              setSuccessMessage(null);
              setIsEditing(true);
            }}
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700 shadow-sm transition"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>Edit Profile</span>
          </button>
        )}
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-emerald-800 text-xs">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">{successMessage}</span>
          </div>
          <button
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-700 hover:text-emerald-900"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* API Error Notification */}
      {apiError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start justify-between text-rose-800 text-xs">
          <div className="flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block">Failed to load or save profile</span>
              <span className="mt-0.5 block">{apiError}</span>
            </div>
          </div>
          <button
            onClick={loadProfile}
            className="ml-4 px-2.5 py-1 rounded bg-rose-100 hover:bg-rose-200 text-rose-900 font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* User Identity Overview Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white font-bold text-lg sm:text-xl flex items-center justify-center shadow-md flex-shrink-0">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-slate-900 truncate max-w-full">{user?.full_name}</h2>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded-full flex-shrink-0">
                Active Candidate
              </span>
            </div>
            <p className="text-xs text-slate-500 font-mono mt-0.5 break-all">{user?.email}</p>
          </div>
          {user?.created_at && (
            <div className="text-left sm:text-right text-[11px] text-slate-400 flex-shrink-0">
              <div className="flex items-center space-x-1 sm:justify-end">
                <Calendar className="w-3.5 h-3.5 flex-shrink-0" />
                <span>Member since {new Date(user.created_at).toLocaleDateString()}</span>
              </div>
              <span className="text-[10px] text-slate-400 block mt-0.5 font-mono">
                ID: {user.id.substring(0, 8)}...
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm text-center">
          <div className="inline-flex items-center space-x-2 text-slate-600 text-sm">
            <Loader2 className="w-5 h-5 animate-spin text-sky-600" />
            <span>Retrieving your career profile from PostgreSQL...</span>
          </div>
        </div>
      )}

      {/* Profile Form (Editing State or Empty State) */}
      {!isLoading && isEditing && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-6 min-w-0">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-100">
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                {profile ? 'Edit Career Profile' : 'Setup Your Career Goals'}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                These settings drive the deterministic matching engine and gap analysis.
              </p>
            </div>
            {profile && (
              <button
                type="button"
                onClick={handleCancel}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {validationError && (
            <div className="mb-5 p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2 text-rose-800 text-xs">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>{validationError}</span>
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Role <span className="text-rose-500">*</span>
                </label>
                <div className="relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="e.g. Senior Backend Engineer"
                    className="block w-full pl-9 pr-3 py-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Total Experience (Years) <span className="text-rose-500">*</span>
                </label>
                <div className="relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Clock className="w-4 h-4" />
                  </div>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="60"
                    required
                    value={experienceYears}
                    onChange={(e) => setExperienceYears(e.target.value)}
                    placeholder="e.g. 3.5"
                    className="block w-full pl-9 pr-3 py-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Professional Headline
              </label>
              <input
                type="text"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Full-Stack Python & React Developer | Distributed Systems"
                className="block w-full px-3 py-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Preferred Location
                </label>
                <div className="relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <MapPin className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={targetLocation}
                    onChange={(e) => setTargetLocation(e.target.value)}
                    placeholder="e.g. Remote, United States / Bengaluru"
                    className="block w-full pl-9 pr-3 py-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Employment Type
                </label>
                <select
                  value={targetEmploymentType}
                  onChange={(e) => setTargetEmploymentType(e.target.value)}
                  className="block w-full px-3 py-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
                >
                  {EMPLOYMENT_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Professional Summary / Bio
              </label>
              <textarea
                rows={4}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Highlight your technical background, career trajectory, key strengths, and learning focus..."
                className="block w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
              {profile && (
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center space-x-2 px-5 py-2 text-xs font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700 shadow-sm transition disabled:opacity-50"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving to Database...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Profile</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* View Mode (Existing Profile) */}
      {!isLoading && !isEditing && profile && (
        <div className="space-y-6">
          {/* Main Targets Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-sm min-w-0">
              <div className="flex items-center space-x-2 text-sky-600 mb-2">
                <Briefcase className="w-4 h-4" />
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Target Role
                </span>
              </div>
              <p className="text-base font-bold text-slate-900 break-words">{profile.target_role}</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-sm min-w-0">
              <div className="flex items-center space-x-2 text-indigo-600 mb-2">
                <Clock className="w-4 h-4" />
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Experience
                </span>
              </div>
              <p className="text-base font-bold text-slate-900 break-words">
                {profile.total_experience_years} {profile.total_experience_years === 1 ? 'Year' : 'Years'}
              </p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-sm min-w-0">
              <div className="flex items-center space-x-2 text-emerald-600 mb-2">
                <MapPin className="w-4 h-4" />
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Preferences
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-800 break-words">
                {profile.target_employment_type || 'Full-time'}
              </p>
              <p className="text-xs text-slate-500 mt-0.5 break-words">
                {profile.target_location || 'Location Not Specified'}
              </p>
            </div>
          </div>

          {/* Headline & Summary */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-6 shadow-sm min-w-0">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Professional Headline
            </h3>
            <p className="text-sm font-semibold text-slate-800 break-words">
              {profile.headline || 'No headline set yet. Click Edit Profile to add one.'}
            </p>

            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mt-6 mb-2">
              Career Bio & Background
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-line break-words">
              {profile.bio || 'No career summary provided yet. Introduce your key strengths and goals.'}
            </p>
          </div>

          {/* Next Step Card */}
          <div className="bg-gradient-to-r from-sky-50 to-indigo-50 border border-sky-200/70 rounded-xl p-4 sm:p-5 min-w-0">
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-sky-100 rounded-lg text-sky-700 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-sky-900">
                  Next Step: Resume Extraction & Job Matching
                </h4>
                <p className="text-xs text-sky-700 mt-1">
                  Upload your PDF resume to extract verified skills into your profile and discover how well your background aligns with curated industry roles.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
