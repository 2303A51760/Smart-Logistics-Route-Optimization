import React from 'react';

export const MapLegend: React.FC = () => {
  return (
    <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 backdrop-blur-md text-[11px] space-y-2 shadow-xl">
      <span className="font-bold text-slate-300 block uppercase tracking-wider text-[10px]">
        Map Markers Legend
      </span>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-400">
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-indigo-950 border border-indigo-500 flex items-center justify-center text-[10px]">
            🏢
          </span>
          <span>Warehouse Hub</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-emerald-950 border border-emerald-500 flex items-center justify-center text-[10px]">
            🧑‍✈️
          </span>
          <span>Available Driver</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-sky-950 border border-sky-500 flex items-center justify-center text-[10px]">
            🚚
          </span>
          <span>In Transit Driver</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-blue-950 border border-blue-500 flex items-center justify-center text-[10px]">
            📦
          </span>
          <span>Delivery Order</span>
        </div>
      </div>
    </div>
  );
};
