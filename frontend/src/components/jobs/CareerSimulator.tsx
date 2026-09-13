import React, { useState } from 'react';
import {
  SimulationResponse,
  TAXONOMY_SKILLS,
} from '../../types/job';
import {
  Sliders,
  RotateCcw,
  Plus,
  X,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Award,
  AlertTriangle,
  Loader2,
  HelpCircle,
} from 'lucide-react';

interface CareerSimulatorProps {
  jobTitle: string;
  jobCompany: string;
  missingSkills: { name: string; required_proficiency: string }[];
  existingSkills: { name: string; proficiency_level: string }[];
  candidateExperienceYears: number;
  addedSkills: { name: string; proficiency_level: string }[];
  modifiedSkills: { name: string; proficiency_level: string }[];
  removedSkills: string[];
  simExperienceYears: number | '';
  isSimulating: boolean;
  simResult: SimulationResponse | null;
  simError: string | null;
  isProfileRequired: boolean;
  onAddSkill: (skill: { name: string; proficiency_level: string }) => void;
  onRemoveAddedSkill: (name: string) => void;
  onModifySkill: (skill: { name: string; proficiency_level: string }) => void;
  onRemoveModifiedSkill: (name: string) => void;
  onToggleRemoveSkill: (name: string) => void;
  onChangeExperience: (years: number | '') => void;
  onRunSimulation: () => void;
  onResetScenario: () => void;
  onNavigateToResume: () => void;
  onNavigateToProfile: () => void;
}

export const CareerSimulator: React.FC<CareerSimulatorProps> = ({
  jobTitle,
  jobCompany,
  missingSkills,
  existingSkills,
  candidateExperienceYears,
  addedSkills,
  modifiedSkills,
  removedSkills,
  simExperienceYears,
  isSimulating,
  simResult,
  simError,
  isProfileRequired,
  onAddSkill,
  onRemoveAddedSkill,
  onModifySkill,
  onRemoveModifiedSkill,
  onToggleRemoveSkill,
  onChangeExperience,
  onRunSimulation,
  onResetScenario,
  onNavigateToResume,
  onNavigateToProfile,
}) => {
  // Local form state for Add Skill
  const [selectedSkillToAdd, setSelectedSkillToAdd] = useState<string>('');
  const [selectedAddProficiency, setSelectedAddProficiency] = useState<string>('intermediate');

  // Local form state for Modify Skill
  const [selectedSkillToMod, setSelectedSkillToMod] = useState<string>('');
  const [selectedModProficiency, setSelectedModProficiency] = useState<string>('advanced');

  // 1. Profile Required State
  if (isProfileRequired) {
    return (
      <div className="p-8 text-center bg-sky-50/60 rounded-xl border border-sky-200">
        <Award className="w-10 h-10 text-sky-600 mx-auto mb-3" />
        <h3 className="text-sm font-bold text-slate-900">Career Profile Required</h3>
        <p className="text-xs text-slate-600 mt-1 max-w-md mx-auto leading-relaxed">
          The What-If Career Simulator requires a baseline profile to calculate accurate score differences and skill interactions. Set up your profile or upload a resume to start testing scenarios.
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

  // Count active modifications
  const hasExpChange =
    typeof simExperienceYears === 'number' &&
    simExperienceYears >= 0 &&
    Math.abs(simExperienceYears - candidateExperienceYears) > 0.05;
  const activeChangesCount =
    addedSkills.length + modifiedSkills.length + removedSkills.length + (hasExpChange ? 1 : 0);

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSkillToAdd) return;
    onAddSkill({
      name: selectedSkillToAdd,
      proficiency_level: selectedAddProficiency,
    });
    setSelectedSkillToAdd('');
  };

  const handleModSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSkillToMod) return;
    onModifySkill({
      name: selectedSkillToMod,
      proficiency_level: selectedModProficiency,
    });
    setSelectedSkillToMod('');
  };

  // Build taxonomy list with missing skills for this job prioritized at top
  const missingSkillNamesSet = new Set(missingSkills.map((s) => s.name.toLowerCase()));
  const missingForJob = TAXONOMY_SKILLS.filter((s) => missingSkillNamesSet.has(s.toLowerCase()));
  const otherTaxonomy = TAXONOMY_SKILLS.filter((s) => !missingSkillNamesSet.has(s.toLowerCase()));

  return (
    <div className="space-y-6 text-slate-800">
      {/* Simulator Intro Banner */}
      <div className="bg-gradient-to-br from-slate-900 via-sky-950 to-slate-900 text-white rounded-xl p-5 shadow-sm">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-sky-300">
            Career Simulator
          </h3>
        </div>
        <p className="text-xs text-slate-200 mt-1.5 max-w-xl leading-relaxed">
          Try a scenario to see how new skills and experience would change your match score. These changes are simulated and will not affect your profile.
        </p>
        <div className="flex items-center space-x-2 mt-3 text-[11px] text-slate-400">
          <span>Target role:</span>
          <span className="font-semibold text-white">{jobTitle}</span>
          <span>at</span>
          <span className="font-semibold text-white">{jobCompany}</span>
        </div>
      </div>

      {/* Simulator Error Banner */}
      {simError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start space-x-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Simulation Error</p>
            <p className="mt-0.5">{simError}</p>
          </div>
        </div>
      )}

      {/* Controls Container */}
      <div className="space-y-5 bg-slate-50 p-5 rounded-xl border border-slate-200">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Try a Scenario ({activeChangesCount} staged)
          </h4>
          {activeChangesCount > 0 && (
            <button
              type="button"
              onClick={onResetScenario}
              className="text-xs text-slate-600 hover:text-slate-900 flex items-center space-x-1 font-semibold transition"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              <span>Reset Scenario</span>
            </button>
          )}
        </div>

        {/* A. Add Known Skill */}
        <div>
          <label className="block text-xs font-bold text-slate-800 mb-1.5">
            Add a Skill
          </label>
          <form onSubmit={handleAddSubmit} className="flex flex-col sm:flex-row gap-2">
            <select
              aria-label="Select a skill to add"
              value={selectedSkillToAdd}
              onChange={(e) => setSelectedSkillToAdd(e.target.value)}
              className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-xs bg-white text-slate-800 focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            >
              <option value="">-- Choose from Curated Taxonomy --</option>
              {missingForJob.length > 0 && (
                <optgroup label="Missing for this job (Recommended)">
                  {missingForJob.map((s) => (
                    <option key={s} value={s}>
                      ⭐ {s}
                    </option>
                  ))}
                </optgroup>
              )}
              <optgroup label="All Taxonomy Skills">
                {otherTaxonomy.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </optgroup>
            </select>

            <select
              aria-label="Select proficiency level"
              value={selectedAddProficiency}
              onChange={(e) => setSelectedAddProficiency(e.target.value)}
              className="w-full sm:w-36 px-3 py-2 border border-slate-300 rounded-lg text-xs bg-white text-slate-800 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 capitalize"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>

            <button
              type="submit"
              disabled={!selectedSkillToAdd}
              className="px-3.5 py-2 bg-sky-600 hover:bg-sky-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-lg transition flex items-center justify-center space-x-1 whitespace-nowrap"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Skill</span>
            </button>
          </form>

          {/* Added Skills Tags */}
          {addedSkills.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {addedSkills.map((s) => (
                <span
                  key={s.name}
                  className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-sky-100 text-sky-900 border border-sky-300"
                >
                  <span>+ {s.name}</span>
                  <span className="text-[10px] text-sky-700 uppercase font-bold">({s.proficiency_level})</span>
                  <button
                    type="button"
                    onClick={() => onRemoveAddedSkill(s.name)}
                    aria-label={`Remove added skill ${s.name}`}
                    className="hover:text-rose-700 transition"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* B. Modify Existing Skill Proficiency */}
        {existingSkills.length > 0 && (
          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1.5">
              Improve a Skill
            </label>
            <form onSubmit={handleModSubmit} className="flex flex-col sm:flex-row gap-2">
              <select
                aria-label="Select existing skill to modify"
                value={selectedSkillToMod}
                onChange={(e) => setSelectedSkillToMod(e.target.value)}
                className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-xs bg-white text-slate-800 focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
              >
                <option value="">-- Choose Profile Skill --</option>
                {existingSkills.map((s) => (
                  <option key={s.name} value={s.name}>
                    {s.name} (Current: {s.proficiency_level})
                  </option>
                ))}
              </select>

              <select
                aria-label="Select new target proficiency"
                value={selectedModProficiency}
                onChange={(e) => setSelectedModProficiency(e.target.value)}
                className="w-full sm:w-36 px-3 py-2 border border-slate-300 rounded-lg text-xs bg-white text-slate-800 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 capitalize"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
              </select>

              <button
                type="submit"
                disabled={!selectedSkillToMod}
                className="px-3.5 py-2 bg-slate-700 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-lg transition flex items-center justify-center space-x-1 whitespace-nowrap"
              >
                <span>Stage Change</span>
              </button>
            </form>

            {/* Modified Skills Tags */}
            {modifiedSkills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2.5">
                {modifiedSkills.map((s) => (
                  <span
                    key={s.name}
                    className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300"
                  >
                    <span>~ {s.name}</span>
                    <span className="text-[10px] text-amber-800 uppercase font-bold">({s.proficiency_level})</span>
                    <button
                      type="button"
                      onClick={() => onRemoveModifiedSkill(s.name)}
                      aria-label={`Remove modified skill ${s.name}`}
                      className="hover:text-rose-700 transition"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* C. Temporarily Remove an Existing Skill */}
        {existingSkills.length > 0 && (
          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1">
              Remove a Skill (Optional)
            </label>
            <p className="text-[11px] text-slate-500 mb-2">
              Click any skill badge to toggle removing it from this simulation scenario:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {existingSkills.map((s) => {
                const isRemoved = removedSkills.includes(s.name);
                return (
                  <button
                    key={s.name}
                    type="button"
                    onClick={() => onToggleRemoveSkill(s.name)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition border flex items-center space-x-1.5 ${
                      isRemoved
                        ? 'bg-rose-100 text-rose-800 border-rose-300 line-through'
                        : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400'
                    }`}
                  >
                    <span>{s.name}</span>
                    {isRemoved && <span className="text-[10px] text-rose-600 no-underline">(Omitted)</span>}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* D. Temporarily Change Experience Years */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="sim-exp-input" className="text-xs font-bold text-slate-800">
              Adjust Experience
            </label>
            <span className="text-[11px] text-slate-500">
              Profile baseline: <strong className="text-slate-700">{candidateExperienceYears.toFixed(1)} yrs</strong>
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <input
              id="sim-exp-input"
              type="number"
              min="0"
              max="40"
              step="0.5"
              value={simExperienceYears}
              onChange={(e) => {
                const val = e.target.value;
                onChangeExperience(val === '' ? '' : parseFloat(val));
              }}
              className="w-36 px-3 py-2 border border-slate-300 rounded-lg text-xs bg-white text-slate-800 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 font-semibold"
              placeholder="e.g. 3.5"
            />
            {hasExpChange && (
              <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200">
                Simulating {Number(simExperienceYears).toFixed(1)} years ({Number(simExperienceYears) > candidateExperienceYears ? '+' : ''}{(Number(simExperienceYears) - candidateExperienceYears).toFixed(1)} yrs)
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons Bar */}
        <div className="pt-3 border-t border-slate-200 flex flex-col sm:flex-row items-center gap-3">
          <button
            type="button"
            onClick={onRunSimulation}
            disabled={isSimulating}
            className="w-full sm:flex-1 py-2.5 px-4 bg-sky-600 hover:bg-sky-700 disabled:opacity-60 text-white font-bold text-xs rounded-xl transition shadow-sm flex items-center justify-center space-x-2"
          >
            {isSimulating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Calculating Projected Match...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>See Projected Match</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onResetScenario}
            disabled={isSimulating || activeChangesCount === 0}
            className="w-full sm:w-auto py-2.5 px-4 bg-white hover:bg-slate-100 disabled:opacity-40 text-slate-700 font-semibold text-xs rounded-xl border border-slate-300 transition flex items-center justify-center space-x-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            <span>Reset Scenario</span>
          </button>
        </div>
      </div>

      {/* Simulation Result Presentation */}
      {simResult && (
        <div className="space-y-5 bg-white p-5 rounded-xl border-2 border-sky-400 shadow-sm">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center space-x-1.5">
              <Sparkles className="w-4 h-4 text-sky-600" />
              <span>Projected Match</span>
            </h4>
            <span className="text-[11px] text-slate-500">
              Based on your simulated scenario
            </span>
          </div>

          {/* 7. Current vs Simulated Match Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Current Match */}
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-center">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Current Match
              </p>
              <p className="text-2xl font-extrabold text-slate-800 mt-1">
                {simResult.current_score.toFixed(1)}%
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">Your actual profile</p>
            </div>

            {/* Simulated Match */}
            <div className="p-3.5 bg-sky-50 rounded-xl border border-sky-200 text-center">
              <p className="text-[10px] font-bold text-sky-700 uppercase tracking-wider">
                Projected Match
              </p>
              <p className="text-2xl font-extrabold text-sky-900 mt-1">
                {simResult.simulated_score.toFixed(1)}%
              </p>
              <p className="text-[10px] text-sky-700 mt-0.5">With staged scenario</p>
            </div>

            {/* Score Delta */}
            <div
              className={`p-3.5 rounded-xl border text-center ${
                simResult.score_delta > 0
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : simResult.score_delta < 0
                  ? 'bg-rose-50 border-rose-200 text-rose-900'
                  : 'bg-slate-50 border-slate-200 text-slate-700'
              }`}
            >
              <p className="text-[10px] font-bold uppercase tracking-wider opacity-80">
                Projected Change
              </p>
              <div className="flex items-center justify-center space-x-1 mt-1">
                {simResult.score_delta > 0 && <TrendingUp className="w-5 h-5 text-emerald-600" />}
                {simResult.score_delta < 0 && <TrendingDown className="w-5 h-5 text-rose-600" />}
                <p className="text-2xl font-extrabold">
                  {simResult.score_delta > 0 ? '+' : ''}
                  {simResult.score_delta.toFixed(1)}%
                </p>
              </div>
              <p className="text-[10px] opacity-80 mt-0.5">
                {simResult.score_delta > 0
                  ? 'Match score improved'
                  : simResult.score_delta < 0
                  ? 'Match score decreased'
                  : 'No net score change'}
              </p>
            </div>
          </div>

          {/* 8. Changed Factors Explanation */}
          {simResult.changed_factors.length > 0 && (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs">
              <p className="font-bold text-slate-900 mb-2 flex items-center space-x-1.5">
                <HelpCircle className="w-4 h-4 text-sky-600" />
                <span>Why did my score change?</span>
              </p>
              <ul className="space-y-1.5 pl-1">
                {simResult.changed_factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start space-x-2 text-slate-700">
                    <span className="text-sky-600 font-bold">•</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Detailed Dimensional Comparison */}
          <div>
            <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Dimensional Before vs After
            </h5>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <p className="text-[10px] text-slate-500 font-semibold">Required Skills</p>
                <p className="font-bold text-slate-900 mt-0.5">
                  {simResult.current_match.required_skills_score.toFixed(0)}% →{' '}
                  <span className={simResult.simulated_match.required_skills_score > simResult.current_match.required_skills_score ? 'text-emerald-600 font-extrabold' : ''}>
                    {simResult.simulated_match.required_skills_score.toFixed(0)}%
                  </span>
                </p>
              </div>

              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <p className="text-[10px] text-slate-500 font-semibold">Experience</p>
                <p className="font-bold text-slate-900 mt-0.5">
                  {simResult.current_match.experience_score.toFixed(0)}% →{' '}
                  <span className={simResult.simulated_match.experience_score > simResult.current_match.experience_score ? 'text-emerald-600 font-extrabold' : ''}>
                    {simResult.simulated_match.experience_score.toFixed(0)}%
                  </span>
                </p>
              </div>

              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <p className="text-[10px] text-slate-500 font-semibold">Matched Required</p>
                <p className="font-bold text-slate-900 mt-0.5">
                  {simResult.current_match.matched_required_skills_count} →{' '}
                  <span className={simResult.simulated_match.matched_required_skills_count > simResult.current_match.matched_required_skills_count ? 'text-emerald-600 font-extrabold' : ''}>
                    {simResult.simulated_match.matched_required_skills_count}
                  </span>{' '}
                  <span className="text-[10px] text-slate-400 font-normal">/ {simResult.simulated_match.total_required_skills_count}</span>
                </p>
              </div>

              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <p className="text-[10px] text-slate-500 font-semibold">Education</p>
                <p className="font-bold text-slate-900 mt-0.5">
                  {simResult.simulated_match.education_score.toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
