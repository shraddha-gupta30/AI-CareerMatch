import { create } from 'zustand';

export type AppRoute =
  | '/'
  | '/login'
  | '/register'
  | '/dashboard'
  | '/profile'
  | '/resume'
  | '/jobs'
  | '/health';

interface NavigationState {
  currentPath: string;
  targetJobId: string | null;
  targetTab: 'overview' | 'match' | 'gaps' | 'simulator' | 'roadmap' | null;
  navigate: (path: string) => void;
  navigateToJob: (
    jobId: string,
    tab?: 'overview' | 'match' | 'gaps' | 'simulator' | 'roadmap'
  ) => void;
  clearJobTarget: () => void;
}

function getInitialPath(): string {
  if (typeof window !== 'undefined') {
    const path = window.location.pathname;
    if (path.startsWith('/login')) return '/login';
    if (path.startsWith('/register')) return '/register';
    if (path.startsWith('/dashboard')) return '/dashboard';
    if (path.startsWith('/profile')) return '/profile';
    if (path.startsWith('/resume')) return '/resume';
    if (path.startsWith('/jobs')) return '/jobs';
    if (path.startsWith('/health')) return '/health';
    return '/';
  }
  return '/';
}

export const useNavigationStore = create<NavigationState>((set) => {
  // Listen to browser forward/backward navigation
  if (typeof window !== 'undefined') {
    window.addEventListener('popstate', () => {
      set({ currentPath: window.location.pathname });
    });
  }

  return {
    currentPath: getInitialPath(),
    targetJobId: null,
    targetTab: null,
    navigate: (path: string) => {
      if (typeof window !== 'undefined' && window.location.pathname !== path) {
        window.history.pushState({}, '', path);
      }
      set({ currentPath: path });
    },
    navigateToJob: (jobId: string, tab = 'match') => {
      if (typeof window !== 'undefined' && window.location.pathname !== '/jobs') {
        window.history.pushState({}, '', '/jobs');
      }
      set({
        currentPath: '/jobs',
        targetJobId: jobId,
        targetTab: tab,
      });
    },
    clearJobTarget: () => {
      set({ targetJobId: null, targetTab: null });
    },
  };
});
