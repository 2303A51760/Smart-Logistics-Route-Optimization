import React from 'react';

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: string | React.ReactNode;
  color?: 'blue' | 'emerald' | 'amber' | 'rose' | 'purple' | 'cyan';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  change,
  changeType = 'positive',
  icon,
  color = 'blue',
}) => {
  const colorMap = {
    blue: 'from-blue-500/20 to-indigo-500/10 border-blue-500/30 text-blue-400',
    emerald: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/30 text-emerald-400',
    amber: 'from-amber-500/20 to-orange-500/10 border-amber-500/30 text-amber-400',
    rose: 'from-rose-500/20 to-pink-500/10 border-rose-500/30 text-rose-400',
    purple: 'from-purple-500/20 to-violet-500/10 border-purple-500/30 text-purple-400',
    cyan: 'from-cyan-500/20 to-blue-500/10 border-cyan-500/30 text-cyan-400',
  };

  const changeColor =
    changeType === 'positive'
      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
      : changeType === 'negative'
      ? 'text-rose-400 bg-rose-500/10 border-rose-500/20'
      : 'text-slate-400 bg-slate-500/10 border-slate-500/20';

  return (
    <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800/80 backdrop-blur-xl shadow-xl hover:border-slate-700 transition-all group flex flex-col justify-between">
      <div className="flex justify-between items-start">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
            {title}
          </span>
          <div className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            {value}
          </div>
        </div>
        <div
          className={`p-3 rounded-xl border bg-gradient-to-br shadow-inner group-hover:scale-110 transition-transform ${colorMap[color]}`}
        >
          <span className="text-xl flex items-center justify-center">{icon}</span>
        </div>
      </div>

      {(subtitle || change) && (
        <div className="mt-4 flex items-center justify-between text-xs pt-3 border-t border-slate-800/60">
          {change && (
            <span className={`px-2 py-0.5 rounded-md border font-semibold ${changeColor}`}>
              {change}
            </span>
          )}
          {subtitle && <span className="text-slate-400">{subtitle}</span>}
        </div>
      )}
    </div>
  );
};
