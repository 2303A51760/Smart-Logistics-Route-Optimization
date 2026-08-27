import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  BarChart3,
  Calendar,
  Layers,
  Cpu,
  RefreshCw,
  Truck,
  Users,
  ShieldCheck,
  AlertTriangle,
  Building2,
  CheckCircle2,
  Sliders,
  Sparkles,
  ArrowUpRight,
  Info,
} from 'lucide-react';
import {
  forecastApi,
  DemandForecastResponse,
  CapacityPlanningResponse,
  WarehouseComparisonResponse,
  DemandAnalyticsResponse,
} from '../services/forecast';
import { logisticsApi } from '../services/logistics';
import { Warehouse } from '../types';
import { Toast } from '../components/Toast';

export const DemandAnalytics: React.FC = () => {
  const [horizon, setHorizon] = useState<number>(7);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string>('');
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);

  const [forecastData, setForecastData] = useState<DemandForecastResponse | null>(null);
  const [capacityData, setCapacityData] = useState<CapacityPlanningResponse | null>(null);
  const [warehouseComparison, setWarehouseComparison] = useState<WarehouseComparisonResponse | null>(null);
  const [analyticsMeta, setAnalyticsMeta] = useState<DemandAnalyticsResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [retraining, setRetraining] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [fc, cap, comp, meta, whs] = await Promise.all([
        forecastApi.getDemandForecast(horizon, selectedWarehouseId || undefined),
        forecastApi.getCapacityPlanning(horizon, selectedWarehouseId || undefined),
        forecastApi.getWarehouseComparison(horizon),
        forecastApi.getDemandAnalytics(),
        logisticsApi.getWarehouses(),
      ]);

      setForecastData(fc);
      setCapacityData(cap);
      setWarehouseComparison(comp);
      setAnalyticsMeta(meta);
      setWarehouses(whs);
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Failed to load demand forecasting telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [horizon, selectedWarehouseId]);

  const handleRetrain = async () => {
    try {
      setRetraining(true);
      const updated = await forecastApi.retrainDemandModel();
      setAnalyticsMeta(updated);
      setToastMessage('Demand forecasting model successfully retrained on chronological orders!');
      loadData();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || 'Retraining failed.');
    } finally {
      setRetraining(false);
    }
  };

  if (loading && !forecastData) {
    return (
      <div className="py-24 text-center text-slate-400">
        <div className="inline-block animate-spin text-3xl mb-3 text-emerald-400">⟳</div>
        <p className="text-sm">Loading AI Demand Forecasting & Capacity Models...</p>
      </div>
    );
  }

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'UNDER_UTILIZED':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40">UNDER-UTILIZED</span>;
      case 'NORMAL':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">OPTIMAL</span>;
      case 'HIGH_UTILIZATION':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">HIGH UTILIZATION</span>;
      case 'OVER_CAPACITY':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">OVER CAPACITY</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400">UNKNOWN</span>;
    }
  };

  const metrics = analyticsMeta?.selected_metrics || { mae: 3.1, rmse: 3.9, mape: 6.8 };
  const forecastItems = forecastData?.forecast || [];
  const maxOrders = Math.max(...forecastItems.map((f) => f.upper_bound || f.predicted_orders), 70);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-emerald-400 font-semibold mb-1">
            <TrendingUp className="w-4 h-4" />
            <span>AI DEMAND FORECASTING & CAPACITY PLANNING</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span>📈</span> Order Demand & Capacity Engine
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Time-series lag and rolling regression models for multi-horizon demand forecasting, fleet utilization, and facility planning.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Horizon Selector */}
          <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
            {[7, 14, 30].map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  horizon === h
                    ? 'bg-emerald-600 text-white shadow-glow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {h} Days
              </button>
            ))}
          </div>

          {/* Warehouse Filter */}
          <select
            value={selectedWarehouseId}
            onChange={(e) => setSelectedWarehouseId(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-xs text-slate-200 font-medium rounded-xl px-3 py-2"
          >
            <option value="">All Warehouses</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>

          {/* Retrain Button */}
          <button
            disabled={retraining}
            onClick={handleRetrain}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-glow transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${retraining ? 'animate-spin' : ''}`} />
            <span>{retraining ? 'RETRAINING...' : 'RETRAIN'}</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 text-xs">
        <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-1.5">
          <span className="text-slate-400 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Forecasted Demand
          </span>
          <p className="text-2xl font-bold font-mono text-slate-100">
            {capacityData?.forecasted_total_demand || 0} <span className="text-xs text-slate-400 font-normal">orders</span>
          </p>
          <p className="text-[11px] text-slate-500">{horizon}-day cumulative volume</p>
        </div>

        <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-1.5">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-blue-400" /> Daily Average
          </span>
          <p className="text-2xl font-bold font-mono text-blue-400">
            {capacityData?.daily_average_demand || 0} <span className="text-xs text-slate-400 font-normal">orders/day</span>
          </p>
          <p className="text-[11px] text-slate-500">Peak: {capacityData?.peak_daily_demand || 0} orders</p>
        </div>

        <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-1.5">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Truck className="w-3.5 h-3.5 text-indigo-400" /> Available Capacity
          </span>
          <p className="text-2xl font-bold font-mono text-indigo-300">
            {capacityData?.available_capacity || 0} <span className="text-xs text-slate-400 font-normal">orders</span>
          </p>
          <p className="text-[11px] text-slate-500">{capacityData?.active_drivers || 2} active drivers</p>
        </div>

        <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-1.5">
          <span className="text-slate-400 flex items-center gap-1.5">
            <BarChart3 className="w-3.5 h-3.5 text-purple-400" /> Fleet Utilization
          </span>
          <p className="text-2xl font-bold font-mono text-purple-300">
            {capacityData?.capacity_utilization_percent || 0}%
          </p>
          <div className="pt-0.5">{getStatusBadge(capacityData?.status)}</div>
        </div>

        <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-1.5">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-amber-400" /> Required Drivers
          </span>
          <p className="text-2xl font-bold font-mono text-amber-400">
            {capacityData?.required_drivers || 0} <span className="text-xs text-slate-400 font-normal">drivers</span>
          </p>
          <p className="text-[11px] text-slate-500">Gap: {capacityData?.capacity_gap || 0} orders</p>
        </div>
      </div>

      {/* Main Forecast Chart & Uncertainty Envelope */}
      <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" /> Multi-Day Order Demand Forecast & Uncertainty Bounds
            </h2>
            <span className="text-xs text-slate-400">
              Shaded band indicates 95% confidence prediction interval (±{((metrics.rmse * 1.96)).toFixed(1)} orders).
            </span>
          </div>

          <div className="flex items-center gap-3 text-[11px] font-mono">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-3 h-3 rounded bg-emerald-500"></span> Predicted Orders
            </span>
            <span className="flex items-center gap-1 text-indigo-400">
              <span className="w-3 h-3 rounded bg-indigo-500/30 border border-indigo-500/60"></span> Confidence Range
            </span>
          </div>
        </div>

        {/* Visual Bar & Envelope Chart */}
        <div className="pt-4 pb-2">
          <div className="grid grid-cols-7 sm:grid-cols-14 gap-2 items-end h-56 border-b border-slate-800 pb-2">
            {forecastItems.map((item, idx) => {
              const heightPct = Math.min(100, Math.round((item.predicted_orders / maxOrders) * 100));
              const lowerPct = Math.min(100, Math.round(((item.lower_bound || item.predicted_orders) / maxOrders) * 100));
              const upperPct = Math.min(100, Math.round(((item.upper_bound || item.predicted_orders) / maxOrders) * 100));
              const bandHeight = Math.max(8, upperPct - lowerPct);

              return (
                <div key={item.date} className="flex flex-col items-center h-full justify-end group relative">
                  {/* Tooltip on hover */}
                  <div className="absolute -top-16 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none bg-slate-950 text-slate-200 text-[10px] p-2 rounded-xl border border-slate-700 shadow-2xl z-20 whitespace-nowrap">
                    <p className="font-bold text-emerald-400">{item.date}</p>
                    <p>Expected: <strong>{item.predicted_orders}</strong> orders</p>
                    <p className="text-slate-400">Range: {item.lower_bound} - {item.upper_bound}</p>
                  </div>

                  {/* Confidence Band Envelope */}
                  <div
                    style={{ height: `${bandHeight}%`, bottom: `${lowerPct}%` }}
                    className="w-full bg-indigo-500/20 border-y border-indigo-500/40 rounded absolute pointer-events-none"
                  ></div>

                  {/* Predicted Value Bar */}
                  <div
                    style={{ height: `${heightPct}%` }}
                    className="w-3/4 bg-gradient-to-t from-emerald-600 to-teal-400 rounded-t-md group-hover:from-emerald-500 group-hover:to-teal-300 transition-all relative z-10"
                  ></div>

                  <span className="text-[9px] font-mono text-slate-400 mt-2 rotate-45 sm:rotate-0 truncate max-w-full">
                    {item.date.slice(5)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex justify-between items-center text-xs text-slate-400 pt-1">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Source: <strong className="text-slate-200">{forecastData?.source === 'ML' ? 'Scikit-Learn Time-Series ML' : 'Analytical Fallback'}</strong>
          </span>
          <span className="font-mono text-[11px]">Model: {forecastData?.model_version}</span>
        </div>
      </div>

      {/* Grid: Left Warehouse Comparison & Right Capacity Planning */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Warehouse Capacity Table (7 Cols) */}
        <div className="lg:col-span-7 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-400" /> Facility & Warehouse Capacity Matrix
            </h2>
            <span className="text-[11px] font-mono text-slate-400">{horizon}-Day Forecast Horizon</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Warehouse Hub</th>
                  <th className="py-2.5 px-3 text-right">Forecasted</th>
                  <th className="py-2.5 px-3 text-right">Capacity</th>
                  <th className="py-2.5 px-3 text-right">Utilization</th>
                  <th className="py-2.5 px-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {warehouseComparison?.warehouses.map((wh) => (
                  <tr key={wh.warehouse_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-3 text-slate-200 font-sans font-medium">{wh.warehouse_name}</td>
                    <td className="py-3 px-3 text-right text-emerald-400 font-bold">{wh.forecasted_demand}</td>
                    <td className="py-3 px-3 text-right text-slate-400">{wh.capacity}</td>
                    <td className="py-3 px-3 text-right font-bold text-purple-300">{wh.utilization_percent}%</td>
                    <td className="py-3 px-3 text-right">{getStatusBadge(wh.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Model Benchmarks & Telemetry (5 Cols) */}
        <div className="lg:col-span-5 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" /> Model Benchmark & Error Telemetry
            </h2>
          </div>

          <div className="space-y-3 text-xs">
            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Selected Architecture:</span>
              <span className="font-bold text-slate-200 font-mono">{analyticsMeta?.selected_model || 'RandomForestRegressor'}</span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 block mb-0.5">MAE (Mean Error)</span>
                <span className="text-base font-bold font-mono text-amber-400">±{metrics.mae}</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 block mb-0.5">RMSE</span>
                <span className="text-base font-bold font-mono text-blue-400">{metrics.rmse}</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 block mb-0.5">Safe MAPE</span>
                <span className="text-base font-bold font-mono text-emerald-400">{metrics.mape}%</span>
              </div>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 space-y-1">
              <span className="text-[11px] font-bold text-indigo-300 flex items-center gap-1">
                <Info className="w-3.5 h-3.5" /> Documented Operational Assumptions:
              </span>
              <p className="text-[11px] text-slate-400">
                Driver capacity assumption: <strong>25 orders / driver / day</strong>.
                Feature inputs strictly shift lag ($T-1, T-7$) and rolling statistics ($7, 14, 30$) to prevent future-data leakage.
              </p>
            </div>
          </div>
        </div>
      </div>

      {toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} />}
    </div>
  );
};
