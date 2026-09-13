import React from 'react';
import { useAuthStore } from '../../store/authStore';
import { useNavigationStore } from '../../store/navigationStore';
import { Compass, LogOut, Menu } from 'lucide-react';

export const TopBar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuthStore();
  const { navigate, toggleMobileMenu } = useNavigationStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-3.5 sm:px-6 sticky top-0 z-30">
      <div className="flex items-center space-x-2 sm:space-x-3">
        {isAuthenticated && (
          <button
            type="button"
            onClick={toggleMobileMenu}
            className="md:hidden p-2 -ml-1 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div
          className="flex items-center space-x-2.5 sm:space-x-3 cursor-pointer select-none"
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        >
          <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-sm flex-shrink-0">
            <Compass className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <span className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">AI CareerMatch</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-2 sm:space-x-4">
        {isAuthenticated && user ? (
          <div className="flex items-center space-x-2 sm:space-x-3 pl-2 sm:pl-3 border-l border-slate-200">
            <div className="flex items-center space-x-2 sm:space-x-2.5">
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-xs flex-shrink-0">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden sm:block text-left max-w-[140px] md:max-w-[200px]">
                <p className="text-xs font-semibold text-slate-800 leading-none truncate">{user.full_name}</p>
                <p className="text-[10px] text-slate-500 leading-none mt-1 font-mono truncate">{user.email}</p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="inline-flex items-center space-x-1 p-1.5 sm:px-2.5 sm:py-1.5 text-xs font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
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
