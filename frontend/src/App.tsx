import React, { useEffect } from 'react';
import { useAuthStore } from './store/authStore';
import { useNavigationStore } from './store/navigationStore';
import { TopBar } from './components/layout/TopBar';
import { Sidebar } from './components/layout/Sidebar';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ProfilePage } from './pages/ProfilePage';
import { ResumePage } from './pages/ResumePage';
import { JobsPage } from './pages/JobsPage';
import { DashboardPage } from './pages/DashboardPage';
import { HealthStatusCard } from './features/health/HealthStatusCard';
import { Layers, Code2, Lock, CheckCircle, Loader2 } from 'lucide-react';

const PIPELINE_STEPS = [
  { step: '1', title: 'Candidate Profile', desc: 'Career goals & technical background', phase: 'Profile' },
  { step: '2', title: 'Resume PDF Parser', desc: 'Structured extraction & skills mapping', phase: 'Resume' },
  { step: '3', title: 'Curated Catalog', desc: '42 curated industry job positions', phase: 'Catalog' },
  { step: '4', title: 'Match Engine', desc: 'Transparent, skill-based score calculation', phase: 'Matching' },
  { step: '5', title: 'Career Simulator', desc: 'Interactive score projection scenarios', phase: 'Simulator' },
  { step: '6', title: 'Career Roadmap', desc: 'Prerequisite-aware milestone plan', phase: 'Roadmap' },
  { step: '7', title: 'Dashboard', desc: 'Integrated candidate command center', phase: 'Dashboard' },
];

export const App: React.FC = () => {
  const { isAuthenticated, isLoading, initialize } = useAuthStore();
  const { currentPath, navigate } = useNavigationStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  // Protected Route Guards
  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated && (currentPath === '/dashboard' || currentPath === '/profile' || currentPath === '/resume')) {
        navigate('/login');
      } else if (isAuthenticated && (currentPath === '/login' || currentPath === '/register')) {
        navigate('/dashboard');
      }
    }
  }, [isAuthenticated, isLoading, currentPath, navigate]);

  // Global Session Bootstrapping Screen
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-700">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-7 h-7 animate-spin text-sky-600" />
          <p className="text-xs font-semibold tracking-wide uppercase text-slate-500">
            Initializing AI CareerMatch Session...
          </p>
        </div>
      </div>
    );
  }

  // Standalone Full-Page Screens
  if (currentPath === '/') {
    return <LandingPage />;
  }

  if (currentPath === '/login' && !isAuthenticated) {
    return <LoginPage />;
  }

  if (currentPath === '/register' && !isAuthenticated) {
    return <RegisterPage />;
  }

  // Application Shell for Protected / App Area
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <TopBar />

      <div className="flex flex-1 min-w-0">
        <Sidebar />

        <main className="flex-1 p-3.5 sm:p-6 lg:p-8 max-w-6xl w-full min-w-0 overflow-x-hidden">
          {currentPath === '/dashboard' && <DashboardPage />}
          {currentPath === '/profile' && <ProfilePage />}
          {currentPath === '/resume' && <ResumePage />}
          {currentPath === '/jobs' && <JobsPage />}

          {currentPath === '/health' && (
            <div className="space-y-8">
              <div>
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                  Platform Foundation & Health Monitor
                </h1>
                <p className="text-sm text-slate-600 mt-1">
                  Real-time status of the local FastAPI backend and PostgreSQL persistence engine.
                </p>
              </div>

              <HealthStatusCard />

              {/* Architecture Pipeline Overview */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2.5">
                    <Layers className="w-5 h-5 text-indigo-600" />
                    <h3 className="text-base font-semibold text-slate-800">Core Product Pipeline</h3>
                  </div>
                  <span className="text-xs font-medium text-slate-500">System Modules</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {PIPELINE_STEPS.map((item) => (
                    <div
                      key={item.step}
                      className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 text-xs font-bold flex items-center justify-center">
                          {item.step}
                        </span>
                        <span className="text-[10px] font-mono text-slate-600 bg-slate-200 px-1.5 py-0.5 rounded">
                          {item.phase}
                        </span>
                      </div>
                      <h4 className="text-xs font-semibold text-slate-900">{item.title}</h4>
                      <p className="text-[11px] text-slate-500 mt-1 leading-normal">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Architectural Invariants */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 bg-white rounded-xl border border-slate-200">
                  <div className="flex items-center space-x-2 text-sky-700 font-semibold text-xs mb-1">
                    <Code2 className="w-4 h-4" />
                    <span>Deterministic Scoring</span>
                  </div>
                  <p className="text-xs text-slate-600">
                    100% reproducible math. Gemini is strictly isolated from calculating or modifying scores.
                  </p>
                </div>

                <div className="p-4 bg-white rounded-xl border border-slate-200">
                  <div className="flex items-center space-x-2 text-indigo-700 font-semibold text-xs mb-1">
                    <Lock className="w-4 h-4" />
                    <span>Secret Isolation</span>
                  </div>
                  <p className="text-xs text-slate-600">
                    Zero API keys in client bundles. All external AI calls strictly originate from backend routes.
                  </p>
                </div>

                <div className="p-4 bg-white rounded-xl border border-slate-200">
                  <div className="flex items-center space-x-2 text-emerald-700 font-semibold text-xs mb-1">
                    <CheckCircle className="w-4 h-4" />
                    <span>Local Windows Ready</span>
                  </div>
                  <p className="text-xs text-slate-600">
                    Uses cross-platform pathlib.Path and local ports with no cloud lock-in or hidden proxies.
                  </p>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
