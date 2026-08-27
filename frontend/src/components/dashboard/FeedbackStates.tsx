import React from 'react';

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 3 }) => {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 bg-slate-900/80 rounded-2xl border border-slate-800" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-80 bg-slate-900/80 rounded-2xl border border-slate-800" />
        <div className="h-80 bg-slate-900/80 rounded-2xl border border-slate-800" />
      </div>
    </div>
  );
};

export const EmptyState: React.FC<{
  title: string;
  description?: string;
  icon?: string;
  action?: React.ReactNode;
}> = ({ title, description, icon = '📦', action }) => {
  return (
    <div className="bg-slate-900/40 p-8 rounded-2xl border border-slate-800 text-center max-w-md mx-auto space-y-3">
      <div className="text-4xl mb-1">{icon}</div>
      <h3 className="text-base font-bold text-slate-200">{title}</h3>
      {description && <p className="text-xs text-slate-400">{description}</p>}
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};

export const ErrorState: React.FC<{
  message?: string;
  onRetry?: () => void;
}> = ({ message = 'Failed to load dashboard metrics.', onRetry }) => {
  return (
    <div className="bg-rose-950/20 border border-rose-800/40 p-6 rounded-2xl text-center max-w-lg mx-auto space-y-3">
      <div className="text-3xl text-rose-400">⚠️</div>
      <h3 className="text-sm font-bold text-rose-300">Dashboard Unavailable</h3>
      <p className="text-xs text-rose-400/80">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl transition-colors shadow-lg shadow-rose-500/20"
        >
          Try Again
        </button>
      )}
    </div>
  );
};
