import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  Clock,
  User as UserIcon,
  AlertTriangle,
  FileText,
  Activity,
  Layers,
  Globe,
  Terminal,
  CheckCircle2,
  XCircle,
  Eye,
  X,
  Calendar,
  Lock,
} from 'lucide-react';
import { auditApi } from '../services/audit';
import { AuditLog, AuditLogSummary } from '../types';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [summary, setSummary] = useState<AuditLogSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination State
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedResourceType, setSelectedResourceType] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 25;

  // Selected Log for JSON Metadata Modal Inspector
  const [inspectLog, setInspectLog] = useState<AuditLog | null>(null);

  const fetchSummary = async () => {
    try {
      setSummaryLoading(true);
      const data = await auditApi.getSummary();
      setSummary(data);
    } catch (err: any) {
      console.error('Failed to load audit summary:', err);
    } finally {
      setSummaryLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {
        page,
        limit,
        search: searchTerm || undefined,
        resource_type: selectedResourceType || undefined,
      };

      if (selectedStatus === 'SUCCESS') {
        params.success = true;
      } else if (selectedStatus === 'FAILURE') {
        params.success = false;
      }

      const res = await auditApi.listLogs(params);
      setLogs(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch enterprise audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [page, selectedResourceType, selectedStatus]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const getActionBadge = (action: string, success: boolean) => {
    if (!success || action.includes('FAILED') || action.includes('BLOCKED') || action.includes('UNAUTHORIZED')) {
      return 'bg-rose-950/80 text-rose-300 border-rose-800/80';
    }
    if (action.includes('LOGIN') || action.includes('REGISTER')) {
      return 'bg-blue-950/80 text-blue-300 border-blue-800/80';
    }
    if (action.includes('OPTIMIZE')) {
      return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80';
    }
    if (action.includes('ORDER')) {
      return 'bg-purple-950/80 text-purple-300 border-purple-800/80';
    }
    if (action.includes('ROUTE')) {
      return 'bg-cyan-950/80 text-cyan-300 border-cyan-800/80';
    }
    if (action.includes('MAINTENANCE')) {
      return 'bg-amber-950/80 text-amber-300 border-amber-800/80';
    }
    return 'bg-slate-800 text-slate-300 border-slate-700';
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-850 to-purple-950/40 border border-slate-800 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-purple-600/20 border border-purple-500/30 text-purple-400 shadow-glow">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              Enterprise Security & Audit Center
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 font-mono font-medium">
                ADMIN RESTRICTED
              </span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Immutable, non-repudiable audit logging for fleet operations, authentication events, and administrative security actions.
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            fetchSummary();
            fetchLogs();
          }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-200 hover:text-white border border-slate-700 transition shadow"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Security KPI Metrics */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Audit Events</span>
              <Activity className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-3xl font-extrabold text-white mt-3 font-mono">
              {summary.total_events.toLocaleString()}
            </div>
            <div className="text-xs text-slate-500 mt-1">Across all services & users</div>
            <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-blue-500/5 rounded-full blur-xl pointer-events-none" />
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Success Rate</span>
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-3xl font-extrabold text-emerald-400 mt-3 font-mono">
              {summary.total_events > 0
                ? `${Math.round((summary.successful_events / summary.total_events) * 100)}%`
                : '100%'}
            </div>
            <div className="text-xs text-emerald-500/80 mt-1">
              {summary.successful_events} successful operations
            </div>
            <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Failed Operations</span>
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div className="text-3xl font-extrabold text-amber-400 mt-3 font-mono">
              {summary.failed_events}
            </div>
            <div className="text-xs text-slate-500 mt-1">Validation & operation failures</div>
            <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Security Incidents</span>
              <Lock className="w-5 h-5 text-rose-400" />
            </div>
            <div className="text-3xl font-extrabold text-rose-400 mt-3 font-mono">
              {summary.unauthorized_attempts}
            </div>
            <div className="text-xs text-rose-400/80 mt-1">Blocked logins & unauthorized attempts</div>
            <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-rose-500/5 rounded-full blur-xl pointer-events-none" />
          </div>
        </div>
      )}

      {/* Role Breakdown and Top Actions Strip */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Actions By Role */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-lg">
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              Audit Distribution by Role
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Object.entries(summary.actions_by_role).map(([role, count]) => (
                <div key={role} className="p-3 rounded-xl bg-slate-850 border border-slate-800">
                  <div className="text-[11px] font-medium text-slate-400 uppercase">{role}</div>
                  <div className="text-xl font-bold text-white mt-1 font-mono">{count}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Actions */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-lg">
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Most Frequent System Actions
            </h3>
            <div className="flex flex-wrap gap-2">
              {summary.top_actions.map((act) => (
                <div
                  key={act.action}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-850 border border-slate-800 text-xs"
                >
                  <span className="font-mono text-slate-300">{act.action}</span>
                  <span className="px-2 py-0.5 rounded-md bg-purple-900/50 text-purple-300 font-bold font-mono text-[11px]">
                    {act.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-lg space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by action, user email, or detail keywords..."
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-850 border border-slate-750 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 transition"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            {/* Resource Type Filter */}
            <select
              value={selectedResourceType}
              onChange={(e) => {
                setSelectedResourceType(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-850 border border-slate-750 text-xs text-slate-300 focus:outline-none focus:border-purple-500"
            >
              <option value="">All Resource Types</option>
              <option value="AUTH">AUTH</option>
              <option value="USER">USER</option>
              <option value="ORDER">ORDER</option>
              <option value="ROUTE">ROUTE</option>
              <option value="VEHICLE">VEHICLE</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="SYSTEM">SYSTEM</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-850 border border-slate-750 text-xs text-slate-300 focus:outline-none focus:border-purple-500"
            >
              <option value="ALL">All Outcomes</option>
              <option value="SUCCESS">Success Only</option>
              <option value="FAILURE">Failures Only</option>
            </select>

            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow transition"
            >
              Search
            </button>
          </div>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Audit Logs Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-850/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-5 py-3.5">Timestamp</th>
                <th className="px-5 py-3.5">Action</th>
                <th className="px-5 py-3.5">User</th>
                <th className="px-5 py-3.5">Resource</th>
                <th className="px-5 py-3.5">IP & Client</th>
                <th className="px-5 py-3.5 text-center">Status</th>
                <th className="px-5 py-3.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-purple-400" />
                    Loading secure audit logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    No audit records matching criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-850/50 transition">
                    <td className="px-5 py-4 whitespace-nowrap font-mono text-slate-400">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      <span
                        className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold border ${getActionBadge(
                          log.action,
                          log.success
                        )}`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      <div>
                        <span className="text-white font-medium">{log.user_email || 'Anonymous / System'}</span>
                        {log.user_role && (
                          <span className="block text-[10px] text-slate-500 font-mono uppercase">{log.user_role}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      <span className="font-mono text-slate-300">{log.resource_type || '-'}</span>
                      {log.resource_id && (
                        <span className="block text-[10px] text-slate-500 font-mono truncate max-w-[140px]">
                          {log.resource_id}
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      <div className="font-mono text-slate-400 flex items-center gap-1.5">
                        <Globe className="w-3 h-3 text-slate-500" />
                        {log.ip_address || '127.0.0.1'}
                      </div>
                      <div className="text-[10px] text-slate-500 truncate max-w-[180px]">
                        {log.user_agent || '-'}
                      </div>
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-center">
                      {log.success ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800/80">
                          <CheckCircle2 className="w-3 h-3" /> SUCCESS
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-950/80 text-rose-300 border border-rose-800/80">
                          <XCircle className="w-3 h-3" /> FAILED
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => setInspectLog(log)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition inline-flex items-center gap-1 text-xs"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 bg-slate-850/50 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing {logs.length > 0 ? (page - 1) * limit + 1 : 0} to{' '}
            {Math.min(page * limit, total)} of {total} events
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 border border-slate-700 transition"
            >
              Previous
            </button>
            <span className="px-2 font-mono text-slate-300">
              Page {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 border border-slate-700 transition"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* JSON Metadata Inspector Modal */}
      {inspectLog && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 animate-scaleUp">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-purple-400" />
                <h3 className="font-bold text-white text-base">Audit Event Inspector: {inspectLog.id}</h3>
              </div>
              <button
                onClick={() => setInspectLog(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-850 p-4 rounded-xl border border-slate-800 font-mono">
              <div>
                <span className="text-slate-500 block">Action:</span>
                <span className="text-white font-semibold">{inspectLog.action}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Timestamp:</span>
                <span className="text-slate-300">{inspectLog.timestamp}</span>
              </div>
              <div>
                <span className="text-slate-500 block">User Email:</span>
                <span className="text-slate-300">{inspectLog.user_email || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">User Role:</span>
                <span className="text-slate-300">{inspectLog.user_role || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">IP Address:</span>
                <span className="text-slate-300">{inspectLog.ip_address || '127.0.0.1'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Status:</span>
                <span className={inspectLog.success ? 'text-emerald-400' : 'text-rose-400'}>
                  {inspectLog.success ? 'SUCCESS' : 'FAILURE'}
                </span>
              </div>
            </div>

            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Event Metadata Payload
              </span>
              <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono text-purple-300 overflow-x-auto max-h-60">
                {inspectLog.details
                  ? (() => {
                      try {
                        return JSON.stringify(JSON.parse(inspectLog.details), null, 2);
                      } catch {
                        return inspectLog.details;
                      }
                    })()
                  : 'No additional details logged.'}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setInspectLog(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;
