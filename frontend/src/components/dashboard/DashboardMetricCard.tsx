import React from 'react';
import { LucideIcon, ArrowRight } from 'lucide-react';

interface DashboardMetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor: string;
  iconBg: string;
  badge?: {
    text: string;
    variant: 'emerald' | 'sky' | 'indigo' | 'amber' | 'slate';
  };
  progress?: {
    current: number;
    max: number;
    percentage: number;
  };
  onClick?: () => void;
  ctaText?: string;
}

const BADGE_STYLES: Record<string, string> = {
  emerald: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  sky: 'bg-sky-100 text-sky-800 border-sky-200',
  indigo: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  amber: 'bg-amber-100 text-amber-800 border-amber-200',
  slate: 'bg-slate-100 text-slate-700 border-slate-200',
};

export const DashboardMetricCard: React.FC<DashboardMetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor,
  iconBg,
  badge,
  progress,
  onClick,
  ctaText,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between transition-all duration-200 ${
        onClick
          ? 'cursor-pointer hover:border-slate-300 hover:shadow-md hover:-translate-y-0.5'
          : ''
      }`}
    >
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            {title}
          </span>
          <div
            className={`w-9 h-9 rounded-xl ${iconBg} ${iconColor} flex items-center justify-center flex-shrink-0`}
          >
            <Icon className="w-5 h-5" />
          </div>
        </div>

        <div className="flex items-baseline space-x-2">
          <span className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            {value}
          </span>
          {badge && (
            <span
              className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                BADGE_STYLES[badge.variant] || BADGE_STYLES.slate
              }`}
            >
              {badge.text}
            </span>
          )}
        </div>

        {subtitle && (
          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{subtitle}</p>
        )}
      </div>

      {progress && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1.5 font-medium">
            <span>Progress</span>
            <span>{progress.percentage.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-sky-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, progress.percentage))}%` }}
            />
          </div>
        </div>
      )}

      {onClick && ctaText && (
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-sky-600 group">
          <span>{ctaText}</span>
          <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
        </div>
      )}
    </div>
  );
};
