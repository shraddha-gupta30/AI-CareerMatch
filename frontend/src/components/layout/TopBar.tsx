import React from 'react';
import { useAuthStore } from '../../store/authStore';
import { useNavigationStore } from '../../store/navigationStore';
import { Compass, Sparkles, LogOut } from 'lucide-react';

export const TopBar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuthStore();
  const { navigate } = useNavigationStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-30">
      <div
        className="flex items-center space-x-3 cursor-pointer select-none"
        onClick={() => navigate(isAuthenticated ? '/profile' : '/')}
      >
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-sm">
          <Compass className="w-5 h-5" />
        </div>
        <div>
          <span className="text-base font-bold text-slate-900 tracking-tight">AI CareerMatch</span>
          <span className="ml-2 px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded-full">
            Phase 5 Active
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden md:flex items-center space-x-1 text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Local Windows Dev</span>
        </div>

        {isAuthenticated && user ? (
          <div className="flex items-center space-x-3 pl-3 border-l border-slate-200">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-xs">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-xs font-semibold text-slate-800 leading-none">{user.full_name}</p>
                <p className="text-[10px] text-slate-500 leading-none mt-1 font-mono">{user.email}</p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="inline-flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
              title="Sign out of account"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => navigate('/login')}
              className="px-3 py-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
            >
              Sign In
            </button>
            <button
              onClick={() => navigate('/register')}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700 shadow-sm transition"
            >
              Register
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
