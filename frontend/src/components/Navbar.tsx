import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Navigation,
  ShieldAlert,
  SlidersHorizontal,
  Truck,
  LogOut,
  User as UserIcon,
  Radio,
  Sparkles,
  Package,
  Users,
  Building2,
  CarFront,
  BarChart3,
  Map,
  Route,
  Zap,
  BrainCircuit,
  TrendingUp,
  Wrench,
  BellRing,
  FileText,
} from 'lucide-react';


import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  onOpenOptimize?: () => void;
  wsConnected?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenOptimize, wsConnected = false }) => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getRoleBadgeStyle = (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-950/80 text-purple-300 border-purple-800/60';
      case 'LOGISTICS_MANAGER':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60';
      case 'DRIVER':
        return 'bg-blue-950/80 text-blue-300 border-blue-800/60';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const isActive = (path: string) => location.pathname === path || (path !== '/' && location.pathname.startsWith(path));

  return (
    <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Dynamic Nav Links */}
        <div className="flex items-center gap-5 flex-wrap">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-white shadow-glow group-hover:scale-105 transition-transform">
              <Navigation className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Smart Logistics
              </span>
            </div>
          </Link>

          {/* Role-Specific Navigation Tabs */}
          {isAuthenticated && user && (
            <div className="flex items-center gap-1 bg-slate-850 p-1 rounded-xl border border-slate-800 text-xs flex-wrap">
              {/* Admin & Logistics Manager Navigation */}
              {(user.role === 'ADMIN' || user.role === 'LOGISTICS_MANAGER') && (
                <>
                  <Link
                    to="/dashboard"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/dashboard') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <BarChart3 className="w-3.5 h-3.5" />
                    Dashboard
                  </Link>

                  <Link
                    to="/optimization"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/optimization') ? 'bg-emerald-600 text-white shadow-glow' : 'text-emerald-400 hover:text-white'
                    }`}
                  >
                    <Zap className="w-3.5 h-3.5" />
                    Optimization
                  </Link>

                  <Link
                    to="/ai-insights"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/ai-insights') || isActive('/ai') ? 'bg-indigo-600 text-white shadow-glow' : 'text-indigo-300 hover:text-white'
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Insights
                  </Link>

                  <Link
                    to="/analytics/eta"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/analytics/eta') ? 'bg-purple-600 text-white shadow-glow' : 'text-purple-300 hover:text-white'
                    }`}
                  >
                    <BrainCircuit className="w-3.5 h-3.5" />
                    AI ETA
                  </Link>

                  <Link
                    to="/analytics/demand"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/analytics/demand') ? 'bg-emerald-600 text-white shadow-glow' : 'text-emerald-300 hover:text-white'
                    }`}
                  >
                    <TrendingUp className="w-3.5 h-3.5" />
                    Demand AI
                  </Link>



                  <Link
                    to="/manager/routes"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/manager/routes') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Route className="w-3.5 h-3.5" />
                    Fleet Routes
                  </Link>

                  <Link
                    to="/map"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/map') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Map className="w-3.5 h-3.5" />
                    Map
                  </Link>

                  <Link
                    to="/orders"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/orders') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Package className="w-3.5 h-3.5" />
                    Orders
                  </Link>

                  <Link
                    to="/drivers"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/drivers') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Truck className="w-3.5 h-3.5" />
                    Drivers
                  </Link>

                  <Link
                    to="/vehicles"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/vehicles') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <CarFront className="w-3.5 h-3.5" />
                    Vehicles
                  </Link>

                  <Link
                    to="/maintenance"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/maintenance') ? 'bg-amber-600 text-white shadow-glow' : 'text-amber-400 hover:text-white'
                    }`}
                  >
                    <Wrench className="w-3.5 h-3.5" />
                    Maintenance
                  </Link>

                  <Link
                    to="/alerts"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/alerts') ? 'bg-rose-600 text-white shadow-glow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <BellRing className="w-3.5 h-3.5" />
                    Alerts
                  </Link>

                  <Link
                    to="/warehouses"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/warehouses') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Building2 className="w-3.5 h-3.5" />
                    Warehouses
                  </Link>

                  <Link
                    to="/customers"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/customers') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Users className="w-3.5 h-3.5" />
                    Customers
                  </Link>

                  {user.role === 'ADMIN' && (
                    <>
                      <Link
                        to="/admin"
                        className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                          location.pathname === '/admin' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        <ShieldAlert className="w-3.5 h-3.5" />
                        Admin
                      </Link>

                      <Link
                        to="/admin/audit"
                        className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                          location.pathname === '/admin/audit' || location.pathname === '/audit-logs'
                            ? 'bg-purple-600 text-white shadow'
                            : 'text-purple-300 hover:text-white'
                        }`}
                      >
                        <FileText className="w-3.5 h-3.5" />
                        Audit Logs
                      </Link>
                    </>
                  )}
                </>
              )}

              {/* Driver Navigation */}
              {user.role === 'DRIVER' && (
                <>
                  <Link
                    to="/driver/dashboard"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/driver/dashboard') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <BarChart3 className="w-3.5 h-3.5" />
                    Dashboard
                  </Link>
                  <Link
                    to="/driver/routes"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/driver/routes') ? 'bg-emerald-600 text-white shadow-glow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Route className="w-3.5 h-3.5" />
                    My Routes
                  </Link>
                  <Link
                    to="/alerts"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/alerts') ? 'bg-rose-600 text-white shadow-glow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <BellRing className="w-3.5 h-3.5" />
                    Alerts
                  </Link>
                  <Link
                    to="/map"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/map') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Map className="w-3.5 h-3.5" />
                    My Map
                  </Link>
                  <Link
                    to="/orders"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      isActive('/orders') ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Package className="w-3.5 h-3.5" />
                    Deliveries
                  </Link>
                  <Link
                    to="/driver"
                    className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                      location.pathname === '/driver' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Truck className="w-3.5 h-3.5" />
                    Cockpit
                  </Link>
                </>
              )}
            </div>
          )}
        </div>

        {/* Right Section: Optimization CTA, WebSocket & Profile Info */}
        <div className="flex items-center gap-3.5 flex-wrap">
          {isAuthenticated && user ? (
            <>
              {/* Notification Bell with Badge */}
              <Link
                to="/alerts"
                title="View Alerts & Notifications"
                className="relative p-2 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition"
              >
                <BellRing className="w-4 h-4 text-amber-400" />
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 rounded-full animate-pulse ring-2 ring-slate-900" />
              </Link>

              {/* Live Telemetry Ping */}
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-850 border border-slate-800 text-xs text-slate-300">
                <Radio className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
                <span className="hidden sm:inline">{wsConnected ? 'Telemetry Active' : 'Connecting'}</span>
              </div>

              {/* User Profile Capsule */}
              <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800">
                <div className="flex flex-col items-end">
                  <span className="text-xs font-semibold text-white">{user.name}</span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border uppercase font-medium ${getRoleBadgeStyle(user.role)}`}>
                    {user.role}
                  </span>
                </div>
                <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
                  <UserIcon className="w-4 h-4" />
                </div>
              </div>

              {/* Logout */}
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-2 rounded-xl bg-slate-800/80 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-700/60 hover:border-rose-800/60 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="px-4 py-1.5 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-glow"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};
