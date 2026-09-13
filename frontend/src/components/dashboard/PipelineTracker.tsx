import React from 'react';
import {
  User,
  FileText,
  Briefcase,
  Sliders,
  Compass,
  CheckCircle2,
  Circle,
  Clock,
  ArrowRight,
} from 'lucide-react';

export interface PipelineStageState {
  hasProfile: boolean;
  hasResume: boolean;
  hasViewedJobs: boolean;
  hasSimulated: boolean;
  hasRoadmap: boolean;
}

interface PipelineTrackerProps {
  stages: PipelineStageState;
  onNavigate: (path: string) => void;
  onNavigateToJobs: (tab?: 'overview' | 'match' | 'gaps' | 'simulator' | 'roadmap') => void;
}

export const PipelineTracker: React.FC<PipelineTrackerProps> = ({
  stages,
  onNavigate,
  onNavigateToJobs,
}) => {
  const steps = [
    {
      id: 1,
      title: 'Career Profile',
      desc: 'Set target role, experience & preferences',
      icon: User,
      isCompleted: stages.hasProfile,
      isInProgress: !stages.hasProfile,
      action: () => onNavigate('/profile'),
      actionText: stages.hasProfile ? 'Edit Profile' : 'Create Profile',
    },
    {
      id: 2,
      title: 'Resume Extraction',
      desc: 'Upload PDF & verify AI-extracted skills',
      icon: FileText,
      isCompleted: stages.hasResume,
      isInProgress: stages.hasProfile && !stages.hasResume,
      action: () => onNavigate('/resume'),
      actionText: stages.hasResume ? 'Manage Resume' : 'Upload Resume',
    },
    {
      id: 3,
      title: 'Job Matches',
      desc: 'Explore curated positions with transparent match scores',
      icon: Briefcase,
      isCompleted: stages.hasProfile,
      isInProgress: stages.hasResume && !stages.hasViewedJobs,
      action: () => onNavigateToJobs('match'),
      actionText: 'Explore Matches',
    },
    {
      id: 4,
      title: 'Career Simulator',
      desc: 'Simulate how new skills improve your match score',
      icon: Sliders,
      isCompleted: stages.hasSimulated,
      isInProgress: stages.hasProfile && !stages.hasSimulated,
      action: () => onNavigateToJobs('simulator'),
      actionText: 'Try Scenarios',
    },
    {
      id: 5,
      title: 'Career Roadmap',
      desc: 'Follow a sequenced learning plan to reach your target role',
      icon: Compass,
      isCompleted: stages.hasRoadmap,
      isInProgress: stages.hasProfile && !stages.hasRoadmap,
      action: () => onNavigateToJobs('roadmap'),
      actionText: stages.hasRoadmap ? 'View Roadmap' : 'Generate Roadmap',
    },
  ];

  const completedCount = steps.filter((s) => s.isCompleted).length;
  const progressPercent = (completedCount / steps.length) * 100;

  return (
    <div className="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-sm min-w-0">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">
            Career Readiness Journey
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Key steps from resume to role readiness
          </p>
        </div>
        <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-full flex-shrink-0">
          {completedCount} / {steps.length} Completed
        </span>
      </div>

      {/* Mini Progress Bar */}
      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-6">
        <div
          className="bg-gradient-to-r from-sky-500 to-indigo-600 h-full rounded-full transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Stepper List */}
      <div className="space-y-3">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <div
              key={step.id}
              className={`p-3 sm:p-3.5 rounded-xl border transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                step.isCompleted
                  ? 'border-emerald-200 bg-emerald-50/30'
                  : step.isInProgress
                  ? 'border-sky-300 bg-sky-50/40'
                  : 'border-slate-200 bg-slate-50/50 opacity-75'
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    step.isCompleted
                      ? 'bg-emerald-100 text-emerald-700'
                      : step.isInProgress
                      ? 'bg-sky-100 text-sky-700'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                    <h4 className="text-xs font-bold text-slate-900 truncate">
                      {step.id}. {step.title}
                    </h4>
                    {step.isCompleted ? (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-semibold text-emerald-700 bg-emerald-100/80 px-1.5 py-0.2 rounded flex-shrink-0">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Done</span>
                      </span>
                    ) : step.isInProgress ? (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-semibold text-sky-700 bg-sky-100/80 px-1.5 py-0.2 rounded flex-shrink-0">
                        <Clock className="w-3 h-3" />
                        <span>Active</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded flex-shrink-0">
                        <Circle className="w-3 h-3" />
                        <span>Pending</span>
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 truncate mt-0.5">
                    {step.desc}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={step.action}
                className={`text-[11px] font-semibold px-2.5 py-1.5 rounded-lg transition flex items-center space-x-1 whitespace-nowrap self-start sm:self-auto flex-shrink-0 ${
                  step.isCompleted
                    ? 'text-slate-700 bg-white border border-slate-200 hover:bg-slate-50'
                    : step.isInProgress
                    ? 'text-white bg-sky-600 hover:bg-sky-700 shadow-sm'
                    : 'text-slate-600 bg-white border border-slate-200 hover:bg-slate-50'
                }`}
              >
                <span>{step.actionText}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
