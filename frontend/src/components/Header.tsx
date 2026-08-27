import React from 'react';
import { Navigation, Radio, Sparkles, Activity } from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  wsConnected: boolean;
  onOpenOptimize: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, wsConnected, onOpenOptimize }) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-white shadow-glow">
            <Navigation className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              Smart Logistics <span className="text-emerald-400 text-xs px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800/60 font-mono">v1.0</span>
            </h1>
            <p className="text-xs text-slate-400">Next-Gen Route Optimization & Live Fleet Telemetry</p>
          </div>
        </div>

        {/* Action Controls & Live Status */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* WebSocket indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <Radio className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
            <span>{wsConnected ? 'Live Telemetry Active' : 'Connecting Stream...'}</span>
          </div>

          {/* System Health Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs">
            <Activity className={`w-3.5 h-3.5 ${isHealthy ? 'text-emerald-400' : 'text-amber-400'}`} />
            <span className={isHealthy ? 'text-emerald-300' : 'text-amber-300'}>
              {health ? (isHealthy ? 'Backend & DB Online' : 'Services Standby') : 'Connecting...'}
            </span>
          </div>

          {/* Optimize CTA */}
          <button
            onClick={onOpenOptimize}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium text-sm transition-all duration-200 shadow-glow hover:shadow-emerald-500/40"
          >
            <Sparkles className="w-4 h-4" />
            Optimize Routes (OR-Tools)
          </button>
        </div>
      </div>
    </header>
  );
};
