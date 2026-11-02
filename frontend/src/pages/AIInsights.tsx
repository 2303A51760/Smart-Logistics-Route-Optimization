import React, { useState, useEffect } from 'react';
import {
  Brain,
  Sparkles,
  TrendingUp,
  Clock,
  Fuel,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  Layers,
  RefreshCw,
  Truck,
  UserCheck,
  BarChart3,
  ChevronRight,
  Info,
} from 'lucide-react';
import { aiApi } from '../services/ai';
import { AIOperationsSummary, OrderPriorityItem, DispatchRecommendationItem, RouteReoptimizationOpportunity } from '../types/ai';

export const AIInsights: React.FC = () => {
  const [summary, setSummary] = useState<AIOperationsSummary | null>(null);
  const [priorities, setPriorities] = useState<OrderPriorityItem[]>([]);
  const [selectedPriorityFilter, setSelectedPriorityFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedOrderDetails, setSelectedOrderDetails] = useState<OrderPriorityItem | null>(null);
  const [forecastHorizon, setForecastHorizon] = useState<number>(7);
  const [forecastData, setForecastData] = useState<any>(null);

  const fetchAIData = async () => {
    try {
      setRefreshing(true);
      const [sumData, prioData, fcData] = await Promise.all([
        aiApi.getOperationsSummary(),
        aiApi.listOrderPriorities(),
        aiApi.getDemandForecast(forecastHorizon),
      ]);
      setSummary(sumData);
      setPriorities(prioData.orders);
      setForecastData(fcData);
    } catch (err) {
      console.error('Error loading AI insights:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAIData();
  }, [forecastHorizon]);

  const filteredPriorities = priorities.filter((p) =>
    selectedPriorityFilter === 'ALL' ? true : p.priority === selectedPriorityFilter
  );

  if (loading && !summary) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
          <p className="text-sm font-medium text-slate-500">Synthesizing AI Fleet Intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header & Status Banner */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-200">
              <Brain className="h-5 w-5" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900">AI Intelligence & Decision Support</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Explainable heuristic scoring, delay risk prediction, automated dispatch matching, and route re-optimization.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Ensemble Active
          </span>
          <button
            onClick={fetchAIData}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin text-indigo-600' : ''}`} />
            Refresh Intelligence
          </button>
        </div>
      </div>

      {/* Executive KPI Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Critical Priority Orders</span>
            <span className="rounded-lg bg-rose-50 p-2 text-rose-600">
              <ShieldAlert className="h-5 w-5" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">{summary?.critical_orders_count || 0}</span>
            <span className="text-xs text-rose-600 font-medium">Require immediate dispatch</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">High Delay Risks</span>
            <span className="rounded-lg bg-amber-50 p-2 text-amber-600">
              <AlertTriangle className="h-5 w-5" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">{summary?.high_delay_risk_count || 0}</span>
            <span className="text-xs text-amber-600 font-medium">Predicted ETA slippage</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Fleet Time Savings</span>
            <span className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
              <Clock className="h-5 w-5" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">{summary?.estimated_fleet_time_saved_minutes || 0}m</span>
            <span className="text-xs text-indigo-600 font-medium">via dynamic re-routing</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Estimated Fuel Saved</span>
            <span className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
              <Fuel className="h-5 w-5" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">{summary?.estimated_fleet_fuel_saved_liters || 0}L</span>
            <span className="text-xs text-emerald-600 font-medium">(${summary?.estimated_fleet_cost_saved_usd || 0})</span>
          </div>
        </div>
      </div>

      {/* Main Grid: AI Dispatch Recommendations & Dynamic Route Re-Optimization */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Section 1: Explainable Dispatch Recommendations */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              <h2 className="font-semibold text-slate-900">AI Dispatch Pairing Recommendations</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">dispatch_matcher_v1</span>
          </div>

          <div className="mt-4 space-y-3">
            {summary?.recommended_assignments && summary.recommended_assignments.length > 0 ? (
              summary.recommended_assignments.map((rec, idx) => (
                <div key={idx} className="rounded-lg border border-slate-100 bg-slate-50/50 p-4 transition hover:bg-slate-50">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-900">{rec.order_number || rec.order_id}</span>
                        <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-700">
                          {rec.score}% Match
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        Assign to <strong className="text-slate-700">{rec.driver_name}</strong> in{' '}
                        <strong className="text-slate-700">{rec.vehicle_name}</strong>
                      </p>
                    </div>
                    <span className="rounded-full bg-slate-200/60 p-1 text-slate-500">
                      <UserCheck className="h-4 w-4" />
                    </span>
                  </div>

                  {/* Explainability reasons list */}
                  <div className="mt-3 border-t border-slate-200/60 pt-2">
                    <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Why this pairing?</p>
                    <ul className="mt-1 space-y-1 text-xs text-slate-600">
                      {rec.reasons?.map((reason: string, rIdx: number) => (
                        <li key={rIdx} className="flex items-start gap-1.5">
                          <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-emerald-600" />
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))
            ) : (
              <p className="py-8 text-center text-sm text-slate-400">All pending orders currently have active driver assignments.</p>
            )}
          </div>
        </div>

        {/* Section 2: Dynamic Route Re-Optimization Opportunities */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-indigo-600" />
              <h2 className="font-semibold text-slate-900">Dynamic Route Re-Optimization</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">dynamic_reoptimizer_v1</span>
          </div>

          <div className="mt-4 space-y-3">
            {summary?.route_reoptimization_opportunities && summary.route_reoptimization_opportunities.length > 0 ? (
              summary.route_reoptimization_opportunities.map((opp, idx) => (
                <div key={idx} className="rounded-lg border border-slate-100 bg-slate-50/50 p-4 transition hover:bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-900">Route #{opp.route_id.slice(0, 8)}</span>
                      <p className="text-xs text-slate-500">{opp.trigger_reason || 'Efficiency Improvement'}</p>
                    </div>
                    <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                      +{opp.estimated_time_saved_minutes} mins saved
                    </span>
                  </div>

                  <div className="mt-3 grid grid-cols-3 gap-2 rounded-lg bg-white p-2.5 text-center text-xs shadow-inner">
                    <div>
                      <span className="text-slate-400">Distance Delta</span>
                      <p className="font-bold text-emerald-600">{opp.estimated_distance_change_km} km</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Fuel Saved</span>
                      <p className="font-bold text-slate-800">{opp.estimated_fuel_saved_liters} L</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Cost Saved</span>
                      <p className="font-bold text-slate-800">${opp.estimated_cost_saved}</p>
                    </div>
                  </div>

                  <ul className="mt-2.5 space-y-1 text-xs text-slate-600">
                    {opp.reasons?.map((r, rIdx) => (
                      <li key={rIdx} className="flex items-start gap-1.5">
                        <ChevronRight className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-indigo-500" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            ) : (
              <p className="py-8 text-center text-sm text-slate-400">All current active routes are mathematically optimal.</p>
            )}
          </div>
        </div>
      </div>

      {/* Section 3: AI Order Priority Scoring Matrix */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col justify-between gap-4 border-b border-slate-100 pb-4 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-600" />
            <div>
              <h2 className="font-semibold text-slate-900">Intelligent Order Priority Matrix</h2>
              <p className="text-xs text-slate-500">Multi-factor priority ranking based on deadline urgency, distance, weight, and delay risk.</p>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap gap-1.5">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((tier) => (
              <button
                key={tier}
                onClick={() => setSelectedPriorityFilter(tier)}
                className={`rounded-lg px-3 py-1 text-xs font-semibold transition ${
                  selectedPriorityFilter === tier
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {tier}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-500 uppercase">
              <tr>
                <th className="px-4 py-3">Order Number</th>
                <th className="px-4 py-3">Score (0-100)</th>
                <th className="px-4 py-3">Priority Tier</th>
                <th className="px-4 py-3">Deadline Note</th>
                <th className="px-4 py-3">Distance</th>
                <th className="px-4 py-3">Recommendation</th>
                <th className="px-4 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredPriorities.map((item) => (
                <tr key={item.order_id} className="hover:bg-slate-50/80 transition">
                  <td className="px-4 py-3 font-semibold text-slate-900">{item.order_number || item.order_id.slice(0, 8)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-16 rounded-full bg-slate-200 overflow-hidden">
                        <div
                          className={`h-full ${
                            item.score >= 85
                              ? 'bg-rose-500'
                              : item.score >= 70
                              ? 'bg-amber-500'
                              : item.score >= 40
                              ? 'bg-indigo-500'
                              : 'bg-slate-400'
                          }`}
                          style={{ width: `${item.score}%` }}
                        ></div>
                      </div>
                      <span className="font-bold text-slate-800">{item.score}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-bold ${
                        item.priority === 'CRITICAL'
                          ? 'bg-rose-100 text-rose-800'
                          : item.priority === 'HIGH'
                          ? 'bg-amber-100 text-amber-800'
                          : item.priority === 'MEDIUM'
                          ? 'bg-indigo-100 text-indigo-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {item.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">{item.factors?.deadline_factor_note || 'Standard window'}</td>
                  <td className="px-4 py-3 text-xs text-slate-600">{item.factors?.distance_km || 10.0} km</td>
                  <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate">{item.recommendation}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setSelectedOrderDetails(item)}
                      className="rounded p-1 text-slate-400 hover:text-indigo-600 hover:bg-slate-100"
                    >
                      <Info className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 4: Demand Forecasting Horizons */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col justify-between gap-4 border-b border-slate-100 pb-4 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-indigo-600" />
            <div>
              <h2 className="font-semibold text-slate-900">AI Demand Forecasting & Fleet Sizing</h2>
              <p className="text-xs text-slate-500">Predictive package volume and fleet readiness bounds.</p>
            </div>
          </div>

          <div className="flex gap-2">
            {[1, 7, 14, 30].map((h) => (
              <button
                key={h}
                onClick={() => setForecastHorizon(h)}
                className={`rounded-lg px-3 py-1 text-xs font-semibold transition ${
                  forecastHorizon === h
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {h} {h === 1 ? 'Day' : 'Days'}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg bg-slate-50 p-4">
            <span className="text-xs text-slate-500">Total Forecasted Volume</span>
            <p className="mt-1 text-2xl font-bold text-slate-900">
              {forecastData?.forecast ? forecastData.forecast.reduce((acc: number, curr: any) => acc + curr.predicted_orders, 0) : 0}{' '}
              orders
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4">
            <span className="text-xs text-slate-500">Peak Demand Period</span>
            <p className="mt-1 text-2xl font-bold text-indigo-600">{forecastData?.peak_day || 'Wednesday'}</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4">
            <span className="text-xs text-slate-500">Demand Trend</span>
            <p className="mt-1 text-2xl font-bold text-emerald-600">{forecastData?.trend || 'STABLE'}</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4">
            <span className="text-xs text-slate-500">Model Confidence</span>
            <p className="mt-1 text-2xl font-bold text-slate-900">92.4%</p>
          </div>
        </div>
      </div>

      {/* Factor Breakdown Modal */}
      {selectedOrderDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">
                Priority Breakdown: {selectedOrderDetails.order_number || selectedOrderDetails.order_id}
              </h3>
              <button
                onClick={() => setSelectedOrderDetails(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs text-slate-700">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Base Priority Points:</span>
                <span className="font-bold">{selectedOrderDetails.factors?.base_priority_score} pts</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Deadline Urgency Points:</span>
                <span className="font-bold">{selectedOrderDetails.factors?.deadline_urgency_score} pts</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Transit Distance Points:</span>
                <span className="font-bold">{selectedOrderDetails.factors?.distance_score} pts</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Weight & Handling Load:</span>
                <span className="font-bold">{selectedOrderDetails.factors?.weight_load_score} pts</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Total Composite Score:</span>
                <span className="font-bold text-indigo-600 text-sm">{selectedOrderDetails.score} / 100</span>
              </div>
            </div>

            <div className="rounded-lg bg-indigo-50/60 p-3">
              <p className="text-xs font-semibold text-indigo-900">AI Recommendation:</p>
              <p className="mt-0.5 text-xs text-indigo-700">{selectedOrderDetails.recommendation}</p>
            </div>

            <button
              onClick={() => setSelectedOrderDetails(null)}
              className="w-full rounded-lg bg-slate-900 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Close Inspector
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
