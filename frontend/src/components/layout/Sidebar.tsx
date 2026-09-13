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
  path: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Jobs & Matches', icon: Briefcase, path: '/jobs' },
  { label: 'Resume', icon: FileText, path: '/resume' },
  { label: 'Career Profile', icon: User, path: '/profile' },
];

export const Sidebar: React.FC = () => {
  const { currentPath, navigate } = useNavigationStore();

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 min-h-[calc(100vh-4rem)] border-r border-slate-800">
      <div className="p-4 flex-1">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-3 mb-3">
          Navigation
        </p>
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentPath === item.path;

            return (
              <button
                key={item.label}
                type="button"
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                  isActive
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-400">
        <button
          type="button"
          onClick={() => navigate('/health')}
          className="flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition text-[11px]"
        >
          <Activity className="w-3.5 h-3.5 text-emerald-500" />
          <span>System Status</span>
        </button>
        <p className="mt-2 text-[10px] text-slate-400">
          AI CareerMatch &copy; 2026
        </p>
      </div>
    </aside>
  );
};
