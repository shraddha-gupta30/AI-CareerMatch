import React from 'react';
import { useNavigationStore } from '../../store/navigationStore';
import { useAuthStore } from '../../store/authStore';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  User,
  Activity,
  X,
  Compass,
  LogOut,
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
  const { currentPath, navigate, isMobileMenuOpen, setMobileMenuOpen } = useNavigationStore();
  const { user, logout } = useAuthStore();

  const handleNavClick = (path: string) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  const handleLogout = () => {
    setMobileMenuOpen(false);
    logout();
    navigate('/login');
  };

  // Nav Items component
  const navContent = (
    <nav className="space-y-1">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = currentPath === item.path;

        return (
          <button
            key={item.label}
            type="button"
            onClick={() => handleNavClick(item.path)}
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
  );

  return (
    <>
      {/* 1. Desktop Persistent Sidebar (>= md) */}
      <aside className="hidden md:flex md:w-64 bg-slate-900 text-slate-300 flex-col flex-shrink-0 min-h-[calc(100vh-4rem)] border-r border-slate-800">
        <div className="p-4 flex-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-3 mb-3">
            Navigation
          </p>
          {navContent}
        </div>

        <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-400">
          <button
            type="button"
            onClick={() => handleNavClick('/health')}
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

      {/* 2. Mobile Slide-Over Drawer (< md) */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Body */}
          <aside className="relative w-72 max-w-[85vw] bg-slate-900 text-slate-300 flex flex-col z-50 shadow-2xl border-r border-slate-800 h-full overflow-y-auto">
            {/* Drawer Header */}
            <div className="h-16 px-4 border-b border-slate-800 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-sm">
                  <Compass className="w-4 h-4" />
                </div>
                <span className="text-sm font-bold text-white tracking-tight">AI CareerMatch</span>
              </div>
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                aria-label="Close navigation"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mobile User Profile Summary */}
            {user && (
              <div className="p-4 border-b border-slate-800/80 bg-slate-950/30">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-full bg-sky-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-sm">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-white truncate">{user.full_name}</p>
                    <p className="text-[10px] text-slate-400 font-mono truncate">{user.email}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Nav Items */}
            <div className="p-4 flex-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-3 mb-3">
                Navigation
              </p>
              {navContent}
            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t border-slate-800/80 space-y-3">
              <button
                type="button"
                onClick={() => handleNavClick('/health')}
                className="w-full flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition text-xs"
              >
                <Activity className="w-4 h-4 text-emerald-500" />
                <span>System Status</span>
              </button>

              {user && (
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-2 text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 px-3 py-2 rounded-xl transition text-xs font-semibold border border-rose-900/30"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              )}

              <p className="text-[10px] text-slate-500 pt-1">
                AI CareerMatch &copy; 2026
              </p>
            </div>
          </aside>
        </div>
      )}
    </>
  );
};
