import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BellRing,
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCheck,
  RotateCw,
  Search,
  Wrench,
  Truck,
  UserX,
  Clock,
  Navigation,
  Package,
  Trash2,
  CheckCircle,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';
import { notificationsApi } from '../services/notifications';
import {
  Notification,
  NotificationSummary,
  AlertType,
  AlertSeverity,
} from '../types';
import { useAuth } from '../context/AuthContext';
import { Toast, ToastType } from '../components/Toast';

export const AlertsCenter: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [summary, setSummary] = useState<NotificationSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [scanning, setScanning] = useState<boolean>(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);

  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const [listRes, sumRes] = await Promise.all([
        notificationsApi.getNotifications({
          unread_only: unreadOnly,
          alert_type: typeFilter || undefined,
          severity: severityFilter || undefined,
        }),
        notificationsApi.getSummary(),
      ]);
      setNotifications(listRes.items);
      setSummary(sumRes);
    } catch (err: any) {
      setToast({
        message: err?.response?.data?.detail || 'Failed to fetch notifications',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [typeFilter, severityFilter, unreadOnly]);

  const handleScanAlerts = async () => {
    try {
      setScanning(true);
      const res = await notificationsApi.triggerAlertAudit();
      setToast({
        message: `Intelligent audit completed: ${res.total_alerts_generated} operational hazard alerts evaluated & dispatched`,
        type: 'success',
      });
      fetchAlerts();
    } catch (err: any) {
      setToast({
        message: err?.response?.data?.detail || 'Failed to run alert scan',
        type: 'error',
      });
    } finally {
      setScanning(false);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await notificationsApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
      );
      if (summary) {
        setSummary({ ...summary, unread_count: Math.max(0, summary.unread_count - 1) });
      }
    } catch (err: any) {
      setToast({ message: 'Failed to mark alert as read', type: 'error' });
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() })));
      if (summary) {
        setSummary({ ...summary, unread_count: 0 });
      }
      setToast({ message: 'All notifications marked as read', type: 'success' });
    } catch (err: any) {
      setToast({ message: 'Failed to mark all as read', type: 'error' });
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      await notificationsApi.dismissNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setToast({ message: 'Notification dismissed', type: 'success' });
    } catch (err: any) {
      setToast({ message: 'Failed to dismiss notification', type: 'error' });
    }
  };

  const filteredNotifications = notifications.filter((n) => {
    const term = searchTerm.toLowerCase();
    return (
      n.title.toLowerCase().includes(term) ||
      n.message.toLowerCase().includes(term) ||
      n.alert_type.toLowerCase().includes(term)
    );
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return {
          badge: 'bg-rose-950/80 text-rose-400 border-rose-800/60',
          icon: <AlertOctagon className="w-4 h-4 text-rose-400 animate-pulse" />,
          cardBorder: 'border-l-4 border-l-rose-500',
        };
      case 'WARNING':
        return {
          badge: 'bg-amber-950/80 text-amber-400 border-amber-800/60',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          cardBorder: 'border-l-4 border-l-amber-500',
        };
      case 'ERROR':
        return {
          badge: 'bg-red-950/80 text-red-400 border-red-800/60',
          icon: <AlertOctagon className="w-4 h-4 text-red-400" />,
          cardBorder: 'border-l-4 border-l-red-500',
        };
      default:
        return {
          badge: 'bg-blue-950/80 text-blue-400 border-blue-800/60',
          icon: <Info className="w-4 h-4 text-blue-400" />,
          cardBorder: 'border-l-4 border-l-blue-500',
        };
    }
  };

  const getAlertTypeIcon = (type: string) => {
    switch (type) {
      case 'MAINTENANCE_DUE':
        return <Wrench className="w-4 h-4 text-amber-400" />;
      case 'VEHICLE_OVERLOADED':
        return <Truck className="w-4 h-4 text-rose-400" />;
      case 'DRIVER_UNAVAILABLE':
        return <UserX className="w-4 h-4 text-purple-400" />;
      case 'DELIVERY_DELAYED':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'ROUTE_EXCEEDS_MAX_DISTANCE':
        return <Navigation className="w-4 h-4 text-cyan-400" />;
      case 'URGENT_ORDER_UNASSIGNED':
        return <Package className="w-4 h-4 text-rose-400" />;
      default:
        return <ShieldAlert className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-500 text-white shadow-glow">
              <BellRing className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Intelligent Logistics Alerts & Notifications
              </h1>
              <p className="text-sm text-slate-400">
                Live automated telemetry hazard monitoring, maintenance alerts, and operational exceptions
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {(user?.role === 'ADMIN' || user?.role === 'LOGISTICS_MANAGER') && (
            <button
              onClick={handleScanAlerts}
              disabled={scanning}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold flex items-center gap-2 shadow-glow transition transform hover:scale-[1.02] disabled:opacity-50"
            >
              <RotateCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
              {scanning ? 'Scanning Fleet...' : 'Run Intelligent Audit'}
            </button>
          )}

          {notifications.some((n) => !n.is_read) && (
            <button
              onClick={handleMarkAllRead}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium flex items-center gap-2 border border-slate-700 transition"
            >
              <CheckCheck className="w-4 h-4 text-emerald-400" />
              Mark All as Read
            </button>
          )}
        </div>
      </div>

      {/* Quick Stats Banner */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex items-center gap-3.5">
            <div className="p-2.5 rounded-xl bg-blue-950/70 border border-blue-800/40 text-blue-400">
              <BellRing className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-400 block font-medium">Unread Alerts</span>
              <span className="text-xl font-bold text-white">{summary.unread_count}</span>
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex items-center gap-3.5">
            <div className="p-2.5 rounded-xl bg-rose-950/70 border border-rose-800/40 text-rose-400">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-400 block font-medium">Critical</span>
              <span className="text-xl font-bold text-rose-400">
                {summary.by_severity['CRITICAL'] || 0}
              </span>
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex items-center gap-3.5">
            <div className="p-2.5 rounded-xl bg-amber-950/70 border border-amber-800/40 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-400 block font-medium">Warnings</span>
              <span className="text-xl font-bold text-amber-400">
                {summary.by_severity['WARNING'] || 0}
              </span>
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex items-center gap-3.5">
            <div className="p-2.5 rounded-xl bg-purple-950/70 border border-purple-800/40 text-purple-400">
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-400 block font-medium">Maintenance Due</span>
              <span className="text-xl font-bold text-white">
                {summary.by_type['MAINTENANCE_DUE'] || 0}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Filter Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search alerts by title, vehicle, reason..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap w-full md:w-auto">
          {/* Category Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Alert Types</option>
            <option value="MAINTENANCE_DUE">Maintenance Due</option>
            <option value="VEHICLE_OVERLOADED">Vehicle Overloaded</option>
            <option value="DRIVER_UNAVAILABLE">Driver Unavailable</option>
            <option value="DELIVERY_DELAYED">Delivery Delayed</option>
            <option value="ROUTE_EXCEEDS_MAX_DISTANCE">Route Exceeds Max Distance</option>
            <option value="URGENT_ORDER_UNASSIGNED">Urgent Order Unassigned</option>
            <option value="SYSTEM_ALERT">System Alerts</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>

          {/* Unread Only Toggle */}
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`px-3 py-2 rounded-xl text-xs font-semibold border transition ${
              unreadOnly
                ? 'bg-amber-600 text-white border-amber-500'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
            }`}
          >
            Unread Only
          </button>
        </div>
      </div>

      {/* Alerts Stream List */}
      <div className="space-y-3">
        {loading ? (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
            <RotateCw className="w-6 h-6 animate-spin mx-auto text-amber-500 mb-2" />
            Loading live alert telemetry...
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
            <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-3 opacity-80" />
            <h3 className="text-base font-semibold text-white">All Clear! No Active Alerts</h3>
            <p className="text-xs text-slate-500 mt-1">
              Fleet operations and vehicle telemetry are currently running within optimal safety limits.
            </p>
          </div>
        ) : (
          filteredNotifications.map((notif) => {
            const sevInfo = getSeverityBadge(notif.severity);
            return (
              <div
                key={notif.id}
                className={`bg-slate-900/90 border border-slate-800 rounded-2xl p-4 transition duration-150 hover:bg-slate-850/80 shadow-md ${
                  sevInfo.cardBorder
                } ${notif.is_read ? 'opacity-70' : 'ring-1 ring-amber-500/20'}`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`px-2 py-0.5 rounded-md border text-[11px] font-bold flex items-center gap-1.5 ${sevInfo.badge}`}>
                        {sevInfo.icon}
                        {notif.severity}
                      </span>

                      <span className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-[11px] font-medium text-slate-300 flex items-center gap-1">
                        {getAlertTypeIcon(notif.alert_type)}
                        {notif.alert_type.replace(/_/g, ' ')}
                      </span>

                      {!notif.is_read && (
                        <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" title="Unread" />
                      )}

                      <span className="text-[11px] text-slate-500 font-mono ml-auto sm:ml-0">
                        {new Date(notif.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}{' '}
                        • {new Date(notif.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white pt-1">{notif.title}</h3>
                    <p className="text-xs text-slate-300 leading-relaxed">{notif.message}</p>

                    {/* Context tags */}
                    <div className="flex items-center gap-2 pt-1 flex-wrap text-[11px] text-slate-400">
                      {notif.vehicle_id && (
                        <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                          Vehicle: {notif.vehicle_id}
                        </span>
                      )}
                      {notif.driver_id && (
                        <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                          Driver: {notif.driver_id}
                        </span>
                      )}
                      {notif.order_id && (
                        <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                          Order: {notif.order_id}
                        </span>
                      )}
                      {notif.route_id && (
                        <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                          Route: {notif.route_id}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 self-end sm:self-start pt-2 sm:pt-0">
                    {notif.alert_type === 'MAINTENANCE_DUE' && (user?.role === 'ADMIN' || user?.role === 'LOGISTICS_MANAGER') && (
                      <button
                        onClick={() => navigate('/maintenance')}
                        className="px-2.5 py-1.5 rounded-lg bg-amber-950/80 hover:bg-amber-900 border border-amber-700/60 text-amber-300 text-xs font-semibold flex items-center gap-1 transition"
                      >
                        <Wrench className="w-3.5 h-3.5" />
                        Maintenance
                      </button>
                    )}

                    {notif.order_id && (
                      <button
                        onClick={() => navigate(`/orders/${notif.order_id}`)}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1 transition"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Order
                      </button>
                    )}

                    {!notif.is_read && (
                      <button
                        onClick={() => handleMarkAsRead(notif.id)}
                        title="Mark as Read"
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      >
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                      </button>
                    )}

                    <button
                      onClick={() => handleDismiss(notif.id)}
                      title="Dismiss"
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
