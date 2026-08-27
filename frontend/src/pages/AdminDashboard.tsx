import React, { useState, useEffect } from 'react';
import { ShieldCheck, Users, Activity, Key, Database, Zap, Lock, RefreshCw, BarChart3, SlidersHorizontal } from 'lucide-react';
import { api } from '../services/api';
import { SystemHealth } from '../types';
import { HealthStatus } from '../components/HealthStatus';
import { OperationsDashboard } from './OperationsDashboard';

interface AdminUserRow {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  lastLogin: string;
}

const DEMO_USERS_LIST: AdminUserRow[] = [
  {
    id: 'usr-admin-001',
    name: 'System Administrator',
    email: 'admin@example.com',
    role: 'ADMIN',
    status: 'ACTIVE',
    lastLogin: 'Just now',
  },
  {
    id: 'usr-mgr-002',
    name: 'Logistics Dispatch Manager',
    email: 'manager@example.com',
    role: 'LOGISTICS_MANAGER',
    status: 'ACTIVE',
    lastLogin: '10 mins ago',
  },
  {
    id: 'usr-drv-003',
    name: 'David Driver (NYC)',
    email: 'driver@example.com',
    role: 'DRIVER',
    status: 'ACTIVE',
    lastLogin: '1 hour ago',
  },
];

export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'analytics' | 'admin'>('analytics');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [users] = useState<AdminUserRow[]>(DEMO_USERS_LIST);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await api.getHealth();
      setHealth(data);
    } catch (e) {
      console.warn('Admin health check error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top View Selector */}
      <div className="flex items-center gap-2 bg-slate-900/60 p-1.5 rounded-2xl border border-slate-800 backdrop-blur-xl w-fit">
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
            activeTab === 'analytics'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Operations Analytics
        </button>
        <button
          onClick={() => setActiveTab('admin')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
            activeTab === 'admin'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/25'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          System Administration & RBAC
        </button>
      </div>

      {activeTab === 'analytics' ? (
        <OperationsDashboard />
      ) : (
        <div className="space-y-6">
          {/* Top Banner */}
          <div className="bg-gradient-to-r from-purple-950/60 via-slate-900 to-slate-900 border border-purple-900/40 rounded-3xl p-6 backdrop-blur-md flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3.5 rounded-2xl bg-purple-600 text-white shadow-glow">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-white tracking-tight">System Admin Console</h2>
                  <span className="px-2.5 py-0.5 rounded-full bg-purple-950 border border-purple-800 text-purple-300 text-xs font-mono font-semibold">
                    SUPERADMIN ACCESS
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Full system control: User provisioning, RBAC policy audit, and infrastructure health monitoring.
                </p>
              </div>
            </div>

            <button
              onClick={fetchHealth}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Status
            </button>
          </div>

          {/* Infrastructure Readiness & Health */}
          <HealthStatus health={health} loading={loading} onRefresh={fetchHealth} />

          {/* User Management & RBAC Directory */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-semibold text-white">Platform User Directory & Role Assignment</h3>
              </div>
              <span className="text-xs text-slate-400">{users.length} Active Accounts</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-850/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Assigned Role</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Last Active</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-850/40 transition">
                      <td className="py-3.5 px-4 font-medium text-white flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 font-bold text-xs">
                          {u.name[0]}
                        </div>
                        {u.name}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-400">{u.email}</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border font-mono ${
                            u.role === 'ADMIN'
                              ? 'bg-purple-950/80 text-purple-300 border-purple-800/60'
                              : u.role === 'LOGISTICS_MANAGER'
                              ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60'
                              : 'bg-blue-950/80 text-blue-300 border-blue-800/60'
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center gap-1.5 text-emerald-400 font-medium text-[11px]">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          {u.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">{u.lastLogin}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* RBAC Permissions Matrix */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm">
            <div className="flex items-center gap-2 mb-4">
              <Lock className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-semibold text-white">Role-Based Access Control (RBAC) Matrix</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-850 border border-purple-900/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm text-purple-300">ADMIN</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 border border-purple-800 text-purple-400">Full</span>
                </div>
                <ul className="text-xs text-slate-300 space-y-1.5">
                  <li>&bull; User management & permissions</li>
                  <li>&bull; Database & cache maintenance</li>
                  <li>&bull; Full fleet dispatch & routes</li>
                  <li>&bull; ML & OR-Tools configurations</li>
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-slate-850 border border-emerald-900/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm text-emerald-300">LOGISTICS_MANAGER</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400">Ops</span>
                </div>
                <ul className="text-xs text-slate-300 space-y-1.5">
                  <li>&bull; Fleet & driver dispatching</li>
                  <li>&bull; OR-Tools VRP optimization</li>
                  <li>&bull; Delivery orders management</li>
                  <li>&bull; Real-time map & traffic tracking</li>
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-slate-850 border border-blue-900/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm text-blue-300">DRIVER</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-400">Field</span>
                </div>
                <ul className="text-xs text-slate-300 space-y-1.5">
                  <li>&bull; Assigned delivery stop manifests</li>
                  <li>&bull; Vehicle telemetry streaming</li>
                  <li>&bull; Real-time GPS location check-in</li>
                  <li>&bull; Stop delivery confirmation</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
