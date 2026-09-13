import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../../services/api';
import { CheckCircle2, XCircle, RefreshCw, Server, ShieldCheck, Cpu } from 'lucide-react';

export const HealthStatusCard: React.FC = () => {
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: 2,
    refetchInterval: 15000, // Background poll every 15s
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-sky-50 rounded-lg text-sky-600">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-800">Backend API Connectivity</h3>
            <p className="text-xs text-slate-500">Live health verification via /api/v1/health</p>
          </div>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 transition disabled:opacity-50"
          title="Trigger manual health check"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-sky-600' : ''}`} />
          <span>Ping API</span>
        </button>
      </div>

      <div className="mt-5">
        {isLoading && (
          <div className="flex items-center space-x-3 p-4 bg-slate-50 rounded-lg text-slate-600">
            <div className="w-4 h-4 rounded-full border-2 border-sky-600 border-t-transparent animate-spin"></div>
            <span className="text-sm font-medium">Querying backend service at http://127.0.0.1:8000/api/v1/health...</span>
          </div>
        )}

        {isError && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <XCircle className="w-5 h-5 text-rose-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-semibold text-rose-900">Backend Unavailable</h4>
                <p className="text-xs text-rose-700 mt-1">
                  Could not connect to the FastAPI server. Error:{' '}
                  <span className="font-mono">{error instanceof Error ? error.message : 'Connection failed'}</span>
                </p>
                <div className="mt-3 text-xs text-rose-800 bg-rose-100/70 p-2.5 rounded font-mono">
                  Tip: Start the backend using:
                  <br />
                  <span className="text-slate-900 font-bold">cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {data && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-semibold text-emerald-900">Backend Connected</span>
                    <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-emerald-200 text-emerald-800">
                      HTTP 200 OK
                    </span>
                  </div>
                  <p className="text-xs text-emerald-700 mt-0.5">
                    FastAPI modular monolith operational on local port 8000
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-4 pt-3 border-t border-emerald-200/60 text-xs">
              <div>
                <span className="text-slate-500 block">Service ID</span>
                <span className="font-semibold text-slate-800 font-mono">{data.service}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Version</span>
                <span className="font-semibold text-slate-800 font-mono">v{data.version}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Environment</span>
                <span className="font-semibold text-slate-800 font-mono capitalize">{data.environment}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 text-xs text-slate-500">
        <div className="flex items-center space-x-2 p-2.5 bg-slate-50 rounded-lg">
          <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>CORS whitelisted for localhost:5173</span>
        </div>
        <div className="flex items-center space-x-2 p-2.5 bg-slate-50 rounded-lg">
          <Cpu className="w-4 h-4 text-sky-600 flex-shrink-0" />
          <span>Local Windows pathing via pathlib.Path</span>
        </div>
      </div>
    </div>
  );
};
