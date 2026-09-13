import React from 'react';
import { useNavigationStore } from '../../store/navigationStore';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  User,
  Activity,
} from 'lucide-react';

interface NavItem {
  label: string;
  icon: React.ElementType;
  phase: string;
  path?: string;
  available?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, phase: 'Overview', path: '/dashboard', available: true },
  { label: 'Job Discovery & Match', icon: Briefcase, phase: 'Phase 5', path: '/jobs', available: true },
  { label: 'Resume Review', icon: FileText, phase: 'Phase 4', path: '/resume', available: true },
  { label: 'Career Profile', icon: User, phase: 'Phase 3', path: '/profile', available: true },
  { label: 'System Health', icon: Activity, phase: 'Monitor', path: '/health', available: true },
];

export const Sidebar: React.FC = () => {
  const { currentPath, navigate } = useNavigationStore();

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-3 mb-2">
          Platform Modules
        </p>
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = item.path ? currentPath === item.path : false;

            return (
              <div
                key={item.label}
                onClick={() => {
                  if (item.available && item.path) {
                    navigate(item.path);
                  }
                }}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition ${
                  item.available ? 'cursor-pointer' : 'cursor-not-allowed opacity-60'
                } ${
                  isActive
                    ? 'bg-sky-600 text-white shadow-sm'
                    : item.available
                    ? 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                    : 'text-slate-500'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                    isActive
                      ? 'bg-sky-700 text-sky-100'
                      : item.available
                      ? 'bg-slate-800 text-slate-300'
                      : 'bg-slate-800/50 text-slate-500'
                  }`}
                >
                  {item.phase}
                </span>
              </div>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-4 border-t border-slate-800 text-[11px] text-slate-400">
        <p className="font-semibold text-slate-200 flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Phase 8 Active</span>
        </p>
        <p className="mt-1 leading-relaxed text-slate-400">
          Complete Career Engine with deterministic matching, simulator & DAG roadmap.
        </p>
      </div>
    </aside>
  );
};
