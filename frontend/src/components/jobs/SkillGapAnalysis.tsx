import React from 'react';
import { SkillGapResponse } from '../../types/job';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  GraduationCap,
  Sparkles,
  Loader2,
  Award,
  Sliders,
  Compass,
} from 'lucide-react';

interface SkillGapAnalysisProps {
  gaps: SkillGapResponse | null;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onNavigateToResume: () => void;
  onNavigateToProfile: () => void;
  onSimulateAddSkill: (skillName: string, reqProf: string) => void;
  onSwitchToSimulator: () => void;
  onSwitchToRoadmap?: () => void;
  isProfileRequired: boolean;
}

export const SkillGapAnalysis: React.FC<SkillGapAnalysisProps> = ({
  gaps,
  isLoading,
  error,
  onRetry,
  onNavigateToResume,
  onNavigateToProfile,
  onSimulateAddSkill,
  onSwitchToSimulator,
  onSwitchToRoadmap,
  isProfileRequired,
}) => {
  // 1. Profile Required State
  if (isProfileRequired) {
    return (
      <div className="p-8 text-center bg-sky-50/60 rounded-xl border border-sky-200">
        <Award className="w-10 h-10 text-sky-600 mx-auto mb-3" />
        <h3 className="text-sm font-bold text-slate-900">Career Profile Required</h3>
        <p className="text-xs text-slate-600 mt-1 max-w-md mx-auto leading-relaxed">
          Skill gap analysis compares this position's exact requirements directly against your structured skills, verified education, and work experience. Please set up your profile or upload a resume to unlock instant gap analysis.
        </p>
        <div className="flex items-center justify-center space-x-3 mt-4">
          <button
            type="button"
            onClick={onNavigateToResume}
            className="px-3.5 py-2 bg-sky-600 text-white text-xs font-semibold rounded-lg hover:bg-sky-700 transition"
          >
            Upload Resume
          </button>
          <button
            type="button"
            onClick={onNavigateToProfile}
            className="px-3.5 py-2 bg-white text-slate-700 border border-slate-300 text-xs font-semibold rounded-lg hover:bg-slate-50 transition"
          >
            Edit Profile
          </button>
        </div>
      </div>
    );
  }

  // 2. Loading State
  if (isLoading) {
    return (
      <div className="p-12 text-center text-slate-500">
        <Loader2 className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-2" />
        <p className="text-xs font-medium">Analyzing skill, experience, and education gaps...</p>
      </div>
    );
  }

  // 3. Error State
  if (error) {
    return (
      <div className="p-6 text-center bg-rose-50 rounded-xl border border-rose-200 text-rose-800">
        <AlertTriangle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
        <p className="text-xs font-semibold">{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 px-3.5 py-1.5 bg-rose-600 text-white text-xs font-semibold rounded-lg hover:bg-rose-700 transition"
        >
          Retry Gap Analysis
        </button>
      </div>
    );
  }

  // 4. Empty State
  if (!gaps) {
    return (
      <div className="p-8 text-center text-slate-500">
        <p className="text-xs">No skill gap analysis available for this position.</p>
      </div>
    );
  }

  const {
    overall_score,
    required_skills_score,
    preferred_skills_score,
    experience_score,
    education_score,
    matched_required_skills,
    partial_required_skills,
    missing_required_skills,
    matched_preferred_skills,
    partial_preferred_skills,
    missing_preferred_skills,
    experience_gap,
    education_compatibility,
    total_required_skills_count,
    matched_required_skills_count,
    total_preferred_skills_count,
    matched_preferred_skills_count,
  } = gaps;

  const totalMissing = missing_required_skills.length + missing_preferred_skills.length;

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-sky-950 text-white rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">
              Gap Analysis Summary
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-900/90 text-sky-200 border border-sky-700">
              Overall Match: {overall_score.toFixed(1)}%
            </span>
          </div>
          <h3 className="text-lg font-bold text-white mt-1">
            {totalMissing === 0
              ? 'Complete Skill Coverage'
              : `${missing_required_skills.length} Required Skill Gap${missing_required_skills.length !== 1 ? 's' : ''} Identified`}
          </h3>
          <p className="text-xs text-slate-300 mt-1 max-w-lg leading-relaxed">
            {totalMissing === 0
              ? 'You meet or partially cover all required and preferred technical competencies for this position.'
              : 'Review your skill alignment below. Use the What-If Simulator to test closing these gaps before applying.'}
          </p>
        </div>

        <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 self-stretch sm:self-auto">
          {onSwitchToRoadmap && (
            <button
              type="button"
              onClick={onSwitchToRoadmap}
              className="flex items-center space-x-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg transition shadow-sm whitespace-nowrap justify-center flex-1 sm:flex-none"
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Career Roadmap</span>
            </button>
          )}
          <button
            type="button"
            onClick={onSwitchToSimulator}
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-lg transition shadow-sm whitespace-nowrap justify-center flex-1 sm:flex-none"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Launch Simulator</span>
          </button>
        </div>
      </div>

      {/* 4. Experience Gap Analysis */}
      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5 text-sky-600" />
          <span>Experience gap</span>
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Your Experience</p>
            <p className="text-base font-bold text-slate-900 mt-0.5">
              {experience_gap.candidate_experience_years.toFixed(1)} years
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">From profile & verified history</p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Required Experience</p>
            <p className="text-base font-bold text-slate-900 mt-0.5">
              {experience_gap.job_min_experience_years > 0
                ? `${experience_gap.job_min_experience_years.toFixed(1)} years`
                : '0.0 years (Entry)'}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">Role minimum requirement</p>
          </div>

          <div
            className={`p-3.5 rounded-xl border ${
              experience_gap.experience_gap > 0
                ? 'bg-rose-50/70 border-rose-200 text-rose-900'
                : 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
            }`}
          >
            <p className="text-[10px] font-semibold uppercase">
              {experience_gap.experience_gap > 0 ? 'Experience Gap' : 'Experience Status'}
            </p>
            <div className="flex items-center space-x-1.5 mt-0.5">
              {experience_gap.experience_gap > 0 ? (
                <>
                  <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                  <span className="text-base font-bold">
                    {experience_gap.experience_gap.toFixed(1)} yr gap
                  </span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span className="text-base font-bold">Meets Requirement</span>
                </>
              )}
            </div>
            <p className="text-[10px] mt-0.5 opacity-80">
              Dimension score: {experience_score.toFixed(0)}%
            </p>
          </div>
        </div>

        <p className="text-xs text-slate-600 mt-2.5 px-1 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="font-semibold text-slate-800">Assessment:</span> {experience_gap.experience_gap_text}
        </p>
      </div>

      {/* 5. Education Compatibility Analysis */}
      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
          <GraduationCap className="w-3.5 h-3.5 text-sky-600" />
          <span>Education compatibility</span>
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Your Education</p>
            <p className="text-base font-bold text-slate-900 mt-0.5">
              {education_compatibility.candidate_highest_level}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">Highest credential on file</p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Required Education</p>
            <p className="text-base font-bold text-slate-900 mt-0.5">
              {education_compatibility.required_level}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">Target education tier</p>
          </div>

          <div
            className={`p-3.5 rounded-xl border ${
              education_compatibility.meets_requirement
                ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                : 'bg-amber-50/70 border-amber-200 text-amber-900'
            }`}
          >
            <p className="text-[10px] font-semibold uppercase">Compatibility Status</p>
            <div className="flex items-center space-x-1.5 mt-0.5">
              {education_compatibility.meets_requirement ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span className="text-base font-bold">✓ Meets requirement</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span className="text-base font-bold">⚠ Education gap</span>
                </>
              )}
            </div>
            <p className="text-[10px] mt-0.5 opacity-80">
              Score: {education_score.toFixed(0)}%
            </p>
          </div>
        </div>

        <p className="text-xs text-slate-600 mt-2.5 px-1 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="font-semibold text-slate-800">Evaluation:</span> {education_compatibility.explanation}
        </p>
      </div>

      {/* 3. Required Skills Analysis */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Award className="w-3.5 h-3.5 text-sky-600" />
            <span>Required Skills (Base Weight 50%)</span>
          </h4>
          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
            {matched_required_skills_count} of {total_required_skills_count} matched ({required_skills_score.toFixed(0)}%)
          </span>
        </div>

        {/* Missing Required Skills */}
        {missing_required_skills.length > 0 && (
          <div className="mb-4">
            <h5 className="text-xs font-bold text-rose-800 flex items-center space-x-1.5 mb-2">
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
              <span>Skills to learn: Required ({missing_required_skills.length})</span>
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {missing_required_skills.map((ms, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl border border-rose-200 bg-rose-50/50 flex items-center justify-between gap-2 text-xs"
                >
                  <div>
                    <span className="font-bold text-slate-900">{ms.name}</span>
                    <div className="flex items-center space-x-2 mt-0.5 text-[10px] text-slate-500">
                      <span className="text-rose-700 font-semibold capitalize">
                        Target: {ms.required_proficiency}
                      </span>
                      <span>•</span>
                      <span>Weight: {ms.importance_weight.toFixed(1)}x</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onSimulateAddSkill(ms.name, ms.required_proficiency)}
                    title={`Test adding ${ms.name} in simulator`}
                    className="px-2 py-1 bg-white hover:bg-rose-100 text-rose-700 border border-rose-300 rounded font-semibold text-[11px] transition flex items-center space-x-1 whitespace-nowrap shadow-2xs"
                  >
                    <span>+ Simulate</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Partial / Transferable Required Skills */}
        {partial_required_skills.length > 0 && (
          <div className="mb-4">
            <h5 className="text-xs font-bold text-sky-800 flex items-center space-x-1.5 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Skills to strengthen: Partial / Transferable ({partial_required_skills.length})</span>
            </h5>
            <div className="space-y-2">
              {partial_required_skills.map((ps, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl border border-sky-200 bg-sky-50/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs"
                >
                  <div>
                    <div className="flex items-center space-x-1.5 font-semibold text-slate-900">
                      <span>{ps.candidate_skill_name}</span>
                      <span className="text-slate-400">→</span>
                      <span className="text-sky-800 font-bold">{ps.job_skill_name}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      Explicit taxonomy relationship: {(ps.similarity_weight * 100).toFixed(0)}% related | Candidate has {ps.candidate_proficiency} (needs {ps.required_proficiency})
                    </p>
                  </div>
                  <span className="text-[11px] font-bold text-sky-800 bg-sky-100 border border-sky-200 px-2.5 py-0.5 rounded whitespace-nowrap">
                    {(ps.credit * 100).toFixed(0)}% Partial Credit
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Matched Required Skills */}
        {matched_required_skills.length > 0 && (
          <div>
            <h5 className="text-xs font-bold text-emerald-800 flex items-center space-x-1.5 mb-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Skills you already have: Matched Required ({matched_required_skills.length})</span>
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {matched_required_skills.map((ms, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-bold text-slate-900">{ms.name}</span>
                    <div className="flex items-center space-x-2 mt-0.5 text-[10px] text-slate-500">
                      <span className="text-emerald-700 font-semibold capitalize">
                        {ms.candidate_proficiency}
                      </span>
                      <span>•</span>
                      <span>Target: {ms.required_proficiency}</span>
                    </div>
                  </div>
                  <span className="text-[11px] font-bold text-emerald-800 bg-emerald-100 border border-emerald-200 px-2 py-0.5 rounded">
                    {(ms.credit * 100).toFixed(0)}% Credit
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Preferred Skills Analysis */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>Preferred Skills (Base Weight 20%)</span>
          </h4>
          {total_preferred_skills_count > 0 ? (
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
              {matched_preferred_skills_count} of {total_preferred_skills_count} matched
              {preferred_skills_score !== null ? ` (${preferred_skills_score.toFixed(0)}%)` : ''}
            </span>
          ) : (
            <span className="text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
              None specified (Weight redistributed)
            </span>
          )}
        </div>

        {total_preferred_skills_count === 0 ? (
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-500">
            This job posting has no preferred skills. The 20% preferred dimension weight is redistributed proportionally across required skills, experience, and education.
          </div>
        ) : (
          <div className="space-y-3">
            {/* Missing Preferred */}
            {missing_preferred_skills.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-slate-700 flex items-center space-x-1.5 mb-2">
                  <XCircle className="w-3.5 h-3.5 text-slate-500" />
                  <span>Skills to learn: Preferred ({missing_preferred_skills.length})</span>
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {missing_preferred_skills.map((ps, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-semibold text-slate-700">{ps.name}</span>
                        <p className="text-[10px] text-slate-500 capitalize">
                          Target: {ps.required_proficiency}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => onSimulateAddSkill(ps.name, ps.required_proficiency)}
                        className="px-2 py-0.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded text-[10px] font-semibold transition"
                      >
                        + Simulate
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Partial Preferred */}
            {partial_preferred_skills.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-purple-800 flex items-center space-x-1.5 mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                  <span>Skills to strengthen: Preferred ({partial_preferred_skills.length})</span>
                </h5>
                <div className="space-y-2">
                  {partial_preferred_skills.map((ps, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg border border-purple-200 bg-purple-50/40 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="flex items-center space-x-1.5 font-semibold text-slate-900">
                          <span>{ps.candidate_skill_name}</span>
                          <span className="text-slate-400">→</span>
                          <span className="text-purple-800 font-bold">{ps.job_skill_name}</span>
                        </div>
                        <p className="text-[10px] text-slate-500 mt-0.5">
                          Related skill: {(ps.similarity_weight * 100).toFixed(0)}% related credit
                        </p>
                      </div>
                      <span className="text-[10px] font-bold text-purple-800 bg-purple-100 px-2 py-0.5 rounded">
                        {(ps.credit * 100).toFixed(0)}% Credit
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Matched Preferred */}
            {matched_preferred_skills.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-emerald-800 flex items-center space-x-1.5 mb-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Skills you already have: Preferred ({matched_preferred_skills.length})</span>
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {matched_preferred_skills.map((ps, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg border border-purple-200 bg-purple-50/50 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-semibold text-slate-900">{ps.name}</span>
                        <p className="text-[10px] text-purple-700 capitalize font-medium">
                          {ps.candidate_proficiency}
                        </p>
                      </div>
                      <span className="text-[10px] font-bold text-purple-800 bg-purple-100 px-2 py-0.5 rounded">
                        {(ps.credit * 100).toFixed(0)}% Credit
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 6. Career Roadmap Quick-Action Banner */}
      {onSwitchToRoadmap && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-900 to-slate-900 text-white flex flex-col sm:flex-row items-center justify-between gap-3 shadow-sm border border-indigo-700/50">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-500/20 rounded-xl border border-indigo-400/30">
              <Compass className="w-5 h-5 text-indigo-300" />
            </div>
            <div>
              <p className="text-xs font-bold text-white">Ready to close these skill gaps?</p>
              <p className="text-[11px] text-slate-300">
                Transform these requirements into a personalized 4-stage Career Roadmap with sequenced prerequisites and portfolio projects.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onSwitchToRoadmap}
            className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-slate-950 font-bold text-xs rounded-xl transition shadow whitespace-nowrap self-stretch sm:self-auto text-center"
          >
            Build Career Roadmap →
          </button>
        </div>
      )}
    </div>
  );
};
