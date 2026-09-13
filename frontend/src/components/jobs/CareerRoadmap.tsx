import React, { useState } from 'react';
import {
  Roadmap,
  RoadmapItemPriority,
  RoadmapItemStatus,
} from '../../types/job';
import {
  Compass,
  CheckCircle2,
  Circle,
  Clock,
  BookOpen,
  FolderGit2,
  RefreshCw,
  Layers,
  Loader2,
  Award,
  TrendingUp,
} from 'lucide-react';

interface CareerRoadmapProps {
  roadmap: Roadmap;
  jobTitle: string;
  company: string;
  isRegenerating: boolean;
  onRegenerate: () => void;
  onStatusChange: (itemId: string, newStatus: RoadmapItemStatus) => Promise<void>;
  updatingItemId: string | null;
}

const STAGE_METADATA: Record<
  number,
  { title: string; subtitle: string; badge: string; color: string }
> = {
  1: {
    title: 'Stage 1: Core Prerequisites & Must-Haves',
    subtitle: 'Foundational prerequisites and critical role requirements needed on day one.',
    badge: 'Foundational',
    color: 'border-rose-300 bg-rose-50/40 text-rose-800',
  },
  2: {
    title: 'Stage 2: Secondary & Knowledge Bridging',
    subtitle: 'Transferable skill deltas and core technical specializations.',
    badge: 'Specialization',
    color: 'border-amber-300 bg-amber-50/40 text-amber-800',
  },
  3: {
    title: 'Stage 3: Competitive Advantage (Preferred Skills)',
    subtitle: 'Differentiating competencies to exceed standard job expectations.',
    badge: 'Competitive Edge',
    color: 'border-sky-300 bg-sky-50/40 text-sky-800',
  },
  4: {
    title: 'Stage 4: Capstone Experience & Credentials',
    subtitle: 'Production portfolio deliverables and education credential alignment.',
    badge: 'Capstone Milestones',
    color: 'border-emerald-300 bg-emerald-50/40 text-emerald-800',
  },
};

const PRIORITY_STYLES: Record<RoadmapItemPriority, { label: string; badgeClass: string }> = {
  critical: {
    label: 'Critical Priority',
    badgeClass: 'bg-rose-100 text-rose-800 border-rose-200',
  },
  high: {
    label: 'High Priority',
    badgeClass: 'bg-amber-100 text-amber-800 border-amber-200',
  },
  medium: {
    label: 'Medium Priority',
    badgeClass: 'bg-sky-100 text-sky-800 border-sky-200',
  },
  low: {
    label: 'Low Priority',
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
  },
};

export const CareerRoadmap: React.FC<CareerRoadmapProps> = ({
  roadmap,
  jobTitle,
  company,
  isRegenerating,
  onRegenerate,
  onStatusChange,
  updatingItemId,
}) => {
  const [selectedStageFilter, setSelectedStageFilter] = useState<number | 'all'>('all');

  const { progress, items } = roadmap;

  // Filter items by stage if selected
  const filteredItems = selectedStageFilter === 'all'
    ? items
    : items.filter((it) => it.stage_phase === selectedStageFilter);

  // Group items by stage
  const stages = Array.from(new Set(items.map((it) => it.stage_phase))).sort((a, b) => a - b);

  return (
    <div className="space-y-6">
      {/* 1. Header & Overview Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 text-white p-6 rounded-2xl shadow-md border border-slate-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-700/60">
          <div>
            <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold uppercase tracking-wider mb-1">
              <Compass className="w-4 h-4" />
              <span>Personalized Career Roadmap</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              {roadmap.target_role}
            </h2>
            <p className="text-xs text-slate-300 mt-0.5">
              Tailored preparation path for <span className="font-semibold text-white">{jobTitle}</span> at <span className="font-semibold text-sky-300">{company}</span>
            </p>
          </div>

          <button
            type="button"
            onClick={onRegenerate}
            disabled={isRegenerating}
            className="flex items-center space-x-2 self-start sm:self-auto px-4 py-2 bg-white/10 hover:bg-white/20 active:bg-white/25 border border-white/20 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
            <span>{isRegenerating ? 'Regenerating...' : 'Regenerate Roadmap'}</span>
          </button>
        </div>

        {/* Dynamic Progress Metric Bar */}
        <div className="pt-6">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-semibold text-slate-200 flex items-center space-x-1.5">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Roadmap Readiness Progress</span>
            </span>
            <span className="font-extrabold text-sm text-emerald-400">
              {progress.progress_percentage.toFixed(1)}% Completed
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-700/80 rounded-full h-3 overflow-hidden p-0.5 border border-slate-600">
            <div
              className="bg-gradient-to-r from-sky-400 via-indigo-400 to-emerald-400 h-full rounded-full transition-all duration-500 shadow-sm"
              style={{ width: `${Math.min(100, Math.max(0, progress.progress_percentage))}%` }}
            />
          </div>

          {/* Stats Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl">
              <p className="text-[11px] text-slate-400 font-medium">Total Milestones</p>
              <p className="text-lg font-bold text-white mt-0.5">{progress.total_items}</p>
            </div>

            <div className="bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-xl">
              <p className="text-[11px] text-emerald-300 font-medium flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Completed</span>
              </p>
              <p className="text-lg font-bold text-emerald-400 mt-0.5">{progress.completed_items}</p>
            </div>

            <div className="bg-amber-500/10 border border-amber-500/20 p-3 rounded-xl">
              <p className="text-[11px] text-amber-300 font-medium flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5" />
                <span>In Progress</span>
              </p>
              <p className="text-lg font-bold text-amber-400 mt-0.5">{progress.in_progress_items}</p>
            </div>

            <div className="bg-slate-500/10 border border-slate-500/20 p-3 rounded-xl">
              <p className="text-[11px] text-slate-300 font-medium flex items-center space-x-1">
                <Circle className="w-3.5 h-3.5 text-slate-400" />
                <span>Not Started</span>
              </p>
              <p className="text-lg font-bold text-slate-300 mt-0.5">{progress.not_started_items}</p>
            </div>
          </div>

          {progress.progress_percentage === 100 && (
            <div className="mt-4 p-3 bg-emerald-500/20 border border-emerald-400/30 rounded-xl flex items-center space-x-2 text-xs text-emerald-200">
              <Award className="w-4 h-4 text-emerald-300 flex-shrink-0" />
              <span>
                <strong>Outstanding!</strong> All milestones in this roadmap are completed. You are fully prepared to apply and excel in this role.
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 2. Stage Filter Navigation */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
        <span className="text-slate-400 font-medium text-[11px] mr-1 flex-shrink-0">
          Filter Stages:
        </span>
        <button
          type="button"
          onClick={() => setSelectedStageFilter('all')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition border whitespace-nowrap ${
            selectedStageFilter === 'all'
              ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          All Stages ({items.length})
        </button>
        {stages.map((stageNum) => {
          const count = items.filter((it) => it.stage_phase === stageNum).length;
          const completedCount = items.filter(
            (it) => it.stage_phase === stageNum && it.status === 'completed'
          ).length;
          return (
            <button
              key={stageNum}
              type="button"
              onClick={() => setSelectedStageFilter(stageNum)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition border whitespace-nowrap flex items-center space-x-1.5 ${
                selectedStageFilter === stageNum
                  ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span>Stage {stageNum}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  selectedStageFilter === stageNum
                    ? 'bg-white/20 text-white'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {completedCount}/{count}
              </span>
            </button>
          );
        })}
      </div>

      {/* 3. Stages List */}
      <div className="space-y-8">
        {stages
          .filter((stg) => selectedStageFilter === 'all' || selectedStageFilter === stg)
          .map((stageNum) => {
            const stageMeta = STAGE_METADATA[stageNum] || {
              title: `Stage ${stageNum}`,
              subtitle: 'Structured progression milestone',
              badge: `Phase ${stageNum}`,
              color: 'border-slate-300 bg-slate-50 text-slate-800',
            };
            const stageItems = filteredItems.filter((it) => it.stage_phase === stageNum);

            if (stageItems.length === 0) return null;

            return (
              <div key={stageNum} className="space-y-3">
                {/* Stage Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-200 gap-1">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                        {stageMeta.title}
                      </h3>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${stageMeta.color}`}>
                        {stageMeta.badge}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{stageMeta.subtitle}</p>
                  </div>
                  <div className="text-xs font-semibold text-slate-600">
                    {stageItems.filter((i) => i.status === 'completed').length} of {stageItems.length} completed
                  </div>
                </div>

                {/* Stage Item Cards */}
                <div className="space-y-4 pt-1">
                  {stageItems.map((item) => {
                    const priorityMeta = PRIORITY_STYLES[item.priority] || PRIORITY_STYLES.medium;
                    const isUpdating = updatingItemId === item.id;
                    const isCompleted = item.status === 'completed';
                    const isInProgress = item.status === 'in_progress';

                    return (
                      <div
                        key={item.id}
                        className={`p-5 rounded-2xl border transition shadow-sm ${
                          isCompleted
                            ? 'bg-emerald-50/20 border-emerald-200'
                            : isInProgress
                            ? 'bg-amber-50/20 border-amber-200'
                            : 'bg-white border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        {/* Top Metadata Row */}
                        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
                          <div className="flex flex-wrap items-center gap-2">
                            {/* Sequence Number */}
                            <span className="w-6 h-6 rounded-full bg-slate-800 text-white font-bold text-[11px] flex items-center justify-center">
                              {item.sequence_order}
                            </span>

                            {/* Priority Badge */}
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${priorityMeta.badgeClass}`}>
                              {priorityMeta.label}
                            </span>

                            {/* Estimated Hours */}
                            <span className="text-[11px] font-medium text-slate-600 flex items-center space-x-1 bg-slate-100 px-2 py-0.5 rounded-md">
                              <Clock className="w-3 h-3 text-slate-400" />
                              <span>{item.estimated_hours} hrs est.</span>
                            </span>

                            {/* Prerequisites Pill */}
                            {item.prerequisites && item.prerequisites.length > 0 && (
                              <span className="text-[10px] font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-md flex items-center space-x-1">
                                <Layers className="w-3 h-3 text-indigo-500" />
                                <span>Prerequisite: {item.prerequisites.join(', ')}</span>
                              </span>
                            )}
                          </div>

                          {/* Interactive Status Segmented Controls */}
                          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl border border-slate-200">
                            <button
                              type="button"
                              disabled={isUpdating}
                              onClick={() => onStatusChange(item.id, 'not_started')}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition flex items-center space-x-1 ${
                                item.status === 'not_started'
                                  ? 'bg-white text-slate-800 shadow-sm border border-slate-200'
                                  : 'text-slate-500 hover:text-slate-800'
                              } disabled:opacity-50`}
                            >
                              <Circle className="w-2.5 h-2.5" />
                              <span>Not Started</span>
                            </button>

                            <button
                              type="button"
                              disabled={isUpdating}
                              onClick={() => onStatusChange(item.id, 'in_progress')}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition flex items-center space-x-1 ${
                                item.status === 'in_progress'
                                  ? 'bg-amber-500 text-white shadow-sm font-bold'
                                  : 'text-slate-500 hover:text-slate-800'
                              } disabled:opacity-50`}
                            >
                              <Clock className="w-2.5 h-2.5" />
                              <span>In Progress</span>
                            </button>

                            <button
                              type="button"
                              disabled={isUpdating}
                              onClick={() => onStatusChange(item.id, 'completed')}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition flex items-center space-x-1 ${
                                item.status === 'completed'
                                  ? 'bg-emerald-600 text-white shadow-sm font-bold'
                                  : 'text-slate-500 hover:text-slate-800'
                              } disabled:opacity-50`}
                            >
                              {isUpdating ? (
                                <Loader2 className="w-2.5 h-2.5 animate-spin" />
                              ) : (
                                <CheckCircle2 className="w-2.5 h-2.5" />
                              )}
                              <span>Completed</span>
                            </button>
                          </div>
                        </div>

                        {/* Title & Description */}
                        <div className="mt-3">
                          <h4
                            className={`text-sm font-bold ${
                              isCompleted ? 'text-slate-700 line-through' : 'text-slate-900'
                            }`}
                          >
                            {item.title}
                          </h4>
                          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                            {item.description}
                          </p>
                        </div>

                        {/* Actionable Learning Directive */}
                        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                            <div className="flex items-center space-x-1.5 text-sky-700 font-bold text-[11px] mb-1">
                              <BookOpen className="w-3.5 h-3.5 text-sky-600" />
                              <span>Recommended Learning Action</span>
                            </div>
                            <p className="text-xs text-slate-700 leading-relaxed">
                              {item.recommended_action}
                            </p>
                          </div>

                          {/* Suggested Project Box */}
                          {item.suggested_project && (
                            <div className="p-3 bg-indigo-50/40 rounded-xl border border-indigo-200/70">
                              <div className="flex items-center space-x-1.5 text-indigo-800 font-bold text-[11px] mb-1">
                                <FolderGit2 className="w-3.5 h-3.5 text-indigo-600" />
                                <span>Suggested Portfolio Deliverable</span>
                              </div>
                              <p className="text-xs text-slate-700 leading-relaxed">
                                {item.suggested_project}
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Completed timestamp footnote if applicable */}
                        {item.completed_at && (
                          <p className="text-[10px] text-emerald-700 font-medium mt-3 flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>
                              Completed on {new Date(item.completed_at).toLocaleDateString(undefined, {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                              })}
                            </span>
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
};
