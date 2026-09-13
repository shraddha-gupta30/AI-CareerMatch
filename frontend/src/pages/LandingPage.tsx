import React from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigationStore } from '../store/navigationStore';
import {
  Compass,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Target,
  Sparkles,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { isAuthenticated, user } = useAuthStore();
  const { navigate } = useNavigationStore();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      {/* Landing Navigation Header */}
      <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-30">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-sm">
            <Compass className="w-5 h-5" />
          </div>
          <span className="text-base font-bold text-slate-900 tracking-tight">AI CareerMatch</span>
        </div>

        <div className="flex items-center space-x-3">
          {isAuthenticated ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700 shadow-sm transition"
            >
              <span>Go to Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <>
              <button
                onClick={() => navigate('/login')}
                className="px-3.5 py-2 text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
              >
                Sign In
              </button>
              <button
                onClick={() => navigate('/register')}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700 shadow-sm transition"
              >
                <span>Get Started</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-6 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-semibold mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Intelligent Job Matching & Skill Gap Analysis</span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Bridge the Gap Between Your Skills and Your Dream Career
        </h1>

        <p className="mt-5 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          AI CareerMatch combines objective, verified skill evaluation with targeted AI extraction to give you transparent job alignment scores and structured prerequisite roadmaps.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          {isAuthenticated ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 text-sm font-semibold rounded-xl bg-sky-600 text-white hover:bg-sky-700 shadow-sm transition"
            >
              <span>Go to Dashboard ({user?.full_name})</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <>
              <button
                onClick={() => navigate('/register')}
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 text-sm font-semibold rounded-xl bg-sky-600 text-white hover:bg-sky-700 shadow-sm transition"
              >
                <span>Create Free Account</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => navigate('/login')}
                className="w-full sm:w-auto px-6 py-3 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition"
              >
                Sign In with Email
              </button>
            </>
          )}
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-12 px-6 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mb-4">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 mb-2">Transparent Matching</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Objective matching algorithm with dynamic proportional weight calculation. Every score is explainable down to individual skill proficiencies.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
            <Target className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 mb-2">Career Profile Builder</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Configure your target roles, employment preferences, and verified technical skills. Track your experience and career objectives in one unified dashboard.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 mb-2">100% Local & Secure</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Runs completely locally on your Windows environment with PostgreSQL and FastAPI. Zero vendor lock-in, zero cloud credential leakage.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-8 border-t border-slate-200 bg-white text-center text-xs text-slate-500">
        <p>AI CareerMatch &copy; 2026 — Intelligent Career Navigation Platform</p>
      </footer>
    </div>
  );
};
