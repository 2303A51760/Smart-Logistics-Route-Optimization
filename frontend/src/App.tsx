import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';
import { wsClient } from './services/websocket';

// Route-level code splitting with React.lazy
const Login = React.lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Register = React.lazy(() => import('./pages/Register').then(m => ({ default: m.Register })));
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const ManagerDashboard = React.lazy(() => import('./pages/ManagerDashboard').then(m => ({ default: m.ManagerDashboard })));
const DriverDashboard = React.lazy(() => import('./pages/DriverDashboard').then(m => ({ default: m.DriverDashboard })));
const OperationsDashboard = React.lazy(() => import('./pages/OperationsDashboard').then(m => ({ default: m.OperationsDashboard })));
const LogisticsMap = React.lazy(() => import('./pages/LogisticsMap').then(m => ({ default: m.LogisticsMap })));
const OptimizationConsole = React.lazy(() => import('./pages/OptimizationConsole').then(m => ({ default: m.OptimizationConsole })));
const DriverRoutes = React.lazy(() => import('./pages/DriverRoutes').then(m => ({ default: m.DriverRoutes })));
const DriverActiveRoute = React.lazy(() => import('./pages/DriverActiveRoute').then(m => ({ default: m.DriverActiveRoute })));
const ManagerRoutes = React.lazy(() => import('./pages/ManagerRoutes').then(m => ({ default: m.ManagerRoutes })));
const Unauthorized = React.lazy(() => import('./pages/Unauthorized').then(m => ({ default: m.Unauthorized })));
const Orders = React.lazy(() => import('./pages/Orders').then(m => ({ default: m.Orders })));
const OrderDetail = React.lazy(() => import('./pages/OrderDetail').then(m => ({ default: m.OrderDetail })));
const Drivers = React.lazy(() => import('./pages/Drivers').then(m => ({ default: m.Drivers })));
const DriverDetail = React.lazy(() => import('./pages/DriverDetail').then(m => ({ default: m.DriverDetail })));
const Vehicles = React.lazy(() => import('./pages/Vehicles').then(m => ({ default: m.Vehicles })));
const Warehouses = React.lazy(() => import('./pages/Warehouses').then(m => ({ default: m.Warehouses })));
const Customers = React.lazy(() => import('./pages/Customers').then(m => ({ default: m.Customers })));
const EtaAnalytics = React.lazy(() => import('./pages/EtaAnalytics').then(m => ({ default: m.EtaAnalytics })));
const DemandAnalytics = React.lazy(() => import('./pages/DemandAnalytics').then(m => ({ default: m.DemandAnalytics })));
const MaintenanceDashboard = React.lazy(() => import('./pages/MaintenanceDashboard').then(m => ({ default: m.MaintenanceDashboard })));
const AlertsCenter = React.lazy(() => import('./pages/AlertsCenter').then(m => ({ default: m.AlertsCenter })));
const AuditLogs = React.lazy(() => import('./pages/AuditLogs').then(m => ({ default: m.AuditLogs })));
const AIInsights = React.lazy(() => import('./pages/AIInsights').then(m => ({ default: m.AIInsights })));

const PageLoadingFallback: React.FC = () => (
  <div className="flex h-96 w-full items-center justify-center">
    <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent"></div>
  </div>
);



// Root redirector based on authenticated user's role
const RoleHomeRedirect: React.FC<{
  isOptimizeOpen: boolean;
  setIsOptimizeOpen: (open: boolean) => void;
}> = ({ isOptimizeOpen, setIsOptimizeOpen }) => {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;

  if (user.role === 'ADMIN') {
    return <AdminDashboard />;
  }

  if (user.role === 'LOGISTICS_MANAGER') {
    return (
      <ManagerDashboard
        isOptimizeOpen={isOptimizeOpen}
        setIsOptimizeOpen={setIsOptimizeOpen}
      />
    );
  }

  return <DriverDashboard />;
};

// Main Layout Wrapper
const AppLayout: React.FC = () => {
  const [isOptimizeOpen, setIsOptimizeOpen] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const location = useLocation();

  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  useEffect(() => {
    wsClient.connect();
    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === 'CONNECTION_ESTABLISHED' || msg.type === 'TELEMETRY_HEARTBEAT') {
        setWsConnected(true);
      }
    });

    return () => {
      unsubscribe();
      wsClient.close();
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {!isAuthPage && (
        <Navbar
          onOpenOptimize={() => setIsOptimizeOpen(true)}
          wsConnected={wsConnected}
        />
      )}

      <main className={`flex-1 ${!isAuthPage ? 'max-w-7xl w-full mx-auto px-6 py-6' : ''}`}>
        <React.Suspense fallback={<PageLoadingFallback />}>
          <Routes>
          {/* Public Auth Pages */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Root Role-Aware Route */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <RoleHomeRedirect
                  isOptimizeOpen={isOptimizeOpen}
                  setIsOptimizeOpen={setIsOptimizeOpen}
                />
              </ProtectedRoute>
            }
          />

          {/* Primary Operations Dashboard */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <OperationsDashboard />
              </ProtectedRoute>
            }
          />

          {/* Phase 5: OR-Tools Route Optimization Console */}
          <Route
            path="/optimization"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <OptimizationConsole />
              </ProtectedRoute>
            }
          />

          {/* Phase 8: AI ETA Analytics & ML Model Console */}
          <Route
            path="/analytics/eta"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <EtaAnalytics />
              </ProtectedRoute>
            }
          />

          {/* Phase 9: AI Demand Forecasting & Capacity Planning */}
          <Route
            path="/analytics/demand"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <DemandAnalytics />
              </ProtectedRoute>
            }
          />

          {/* Phase 14: AI Intelligence & Decision Support Dashboard */}
          <Route
            path="/ai-insights"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <AIInsights />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <AIInsights />
              </ProtectedRoute>
            }
          />

          {/* Phase 10: Vehicle Maintenance & Fleet Health */}
          <Route
            path="/maintenance"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <MaintenanceDashboard />
              </ProtectedRoute>
            }
          />

          {/* Phase 10: Intelligent Logistics Alerts & Notifications */}
          <Route
            path="/alerts"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <AlertsCenter />
              </ProtectedRoute>
            }
          />



          {/* Phase 6: Manager Routes Fleet Console */}
          <Route
            path="/routes"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <ManagerRoutes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes/:id"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <DriverActiveRoute />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manager/routes"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <ManagerRoutes />
              </ProtectedRoute>
            }
          />

          {/* Phase 6: Driver Routes & Execution Cockpit */}
          <Route
            path="/driver/routes"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <DriverRoutes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/driver/routes/:id"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <DriverActiveRoute />
              </ProtectedRoute>
            }
          />

          {/* Interactive Logistics Map */}
          <Route
            path="/map"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <LogisticsMap />
              </ProtectedRoute>
            }
          />

          {/* Core Logistics: Orders */}
          <Route
            path="/orders"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <Orders />
              </ProtectedRoute>
            }
          />
          <Route
            path="/orders/:id"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <OrderDetail />
              </ProtectedRoute>
            }
          />

          {/* Core Logistics: Drivers */}
          <Route
            path="/drivers"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <Drivers />
              </ProtectedRoute>
            }
          />
          <Route
            path="/drivers/:id"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <DriverDetail />
              </ProtectedRoute>
            }
          />

          {/* Core Logistics: Vehicles */}
          <Route
            path="/vehicles"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <Vehicles />
              </ProtectedRoute>
            }
          />

          {/* Core Logistics: Warehouses */}
          <Route
            path="/warehouses"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <Warehouses />
              </ProtectedRoute>
            }
          />

          {/* Core Logistics: Customers */}
          <Route
            path="/customers"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <Customers />
              </ProtectedRoute>
            }
          />

          {/* Admin Dashboard & Phase 12 Security Audit Center */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/audit"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AuditLogs />
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit-logs"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AuditLogs />
              </ProtectedRoute>
            }
          />

          {/* Logistics Manager Dashboard */}
          <Route
            path="/manager"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER']}>
                <ManagerDashboard
                  isOptimizeOpen={isOptimizeOpen}
                  setIsOptimizeOpen={setIsOptimizeOpen}
                />
              </ProtectedRoute>
            }
          />

          {/* Driver Cockpit & Dashboards */}
          <Route
            path="/driver"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <DriverDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/driver/dashboard"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'LOGISTICS_MANAGER', 'DRIVER']}>
                <DriverDashboard />
              </ProtectedRoute>
            }
          />

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </React.Suspense>
      </main>

      {!isAuthPage && (
        <footer className="border-t border-slate-900 bg-slate-950/80 px-6 py-4 text-center text-xs text-slate-500">
          Smart Logistics & Route Optimization Platform &bull; Phase 5 & 6 Real-time OR-Tools Engine & Driver Cockpit Active
        </footer>
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
