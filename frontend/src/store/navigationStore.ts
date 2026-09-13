import { create } from 'zustand';

export type AppRoute = '/' | '/login' | '/register' | '/profile' | '/health';

interface NavigationState {
  currentPath: string;
  navigate: (path: string) => void;
}

function getInitialPath(): string {
  if (typeof window !== 'undefined') {
    const path = window.location.pathname;
    if (path.startsWith('/login')) return '/login';
    if (path.startsWith('/register')) return '/register';
    if (path.startsWith('/profile')) return '/profile';
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
    navigate: (path: string) => {
      if (typeof window !== 'undefined' && window.location.pathname !== path) {
        window.history.pushState({}, '', path);
      }
      set({ currentPath: path });
    },
  };
});
