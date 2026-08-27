import React from 'react';
import { Database, Zap, Server, Wifi, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { SystemHealth } from '../types';

interface HealthStatusProps {
  health: SystemHealth | null;
  loading: boolean;
  onRefresh: () => void;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({ health, loading, onRefresh }) => {
  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'degraded':
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      default:
        return <XCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60';
      case 'degraded':
        return 'bg-amber-950/60 text-amber-300 border-amber-800/60';
      default:
        return 'bg-slate-800/60 text-slate-400 border-slate-700/60';
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-white">Infrastructure & Connectivity</h2>
          <p className="text-xs text-slate-400">PostgreSQL, Redis, FastAPI, and Real-Time Gateway</p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700/50 hover:bg-slate-700 transition"
        >
          {loading ? 'Probing...' : 'Refresh Health'}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Backend FastAPI */}
        <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-medium text-slate-200">FastAPI API</span>
            </div>
            {getStatusIcon(health ? 'healthy' : 'degraded')}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-400">{health?.version ? `v${health.version}` : 'Connecting...'}</span>
            <span className={`text-[11px] px-2 py-0.5 rounded-full border ${getStatusBadge(health ? 'healthy' : 'degraded')}`}>
              {health ? 'ONLINE' : 'PENDING'}
            </span>
          </div>
        </div>

        {/* PostgreSQL */}
        <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-medium text-slate-200">PostgreSQL</span>
            </div>
            {getStatusIcon(health?.services.database.status)}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              {health?.services.database.latency_ms ? `${health.services.database.latency_ms}ms` : 'Standby / Fallback'}
            </span>
            <span className={`text-[11px] px-2 py-0.5 rounded-full border ${getStatusBadge(health?.services.database.status)}`}>
              {health?.services.database.status === 'healthy' ? 'CONNECTED' : 'STANDBY'}
            </span>
          </div>
        </div>

        {/* Redis */}
        <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-rose-400" />
              <span className="text-xs font-medium text-slate-200">Redis Cache</span>
            </div>
            {getStatusIcon(health?.services.redis.status)}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              {health?.services.redis.latency_ms ? `${health.services.redis.latency_ms}ms` : 'Standby / Fallback'}
            </span>
            <span className={`text-[11px] px-2 py-0.5 rounded-full border ${getStatusBadge(health?.services.redis.status)}`}>
              {health?.services.redis.status === 'healthy' ? 'CONNECTED' : 'STANDBY'}
            </span>
          </div>
        </div>

        {/* WebSockets */}
        <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Wifi className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-medium text-slate-200">WebSockets</span>
            </div>
            {getStatusIcon('healthy')}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-400">/ws/tracking</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full border bg-emerald-950/60 text-emerald-300 border-emerald-800/60">
              READY
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
