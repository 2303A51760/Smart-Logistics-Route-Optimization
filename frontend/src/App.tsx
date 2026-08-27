import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { AdminDashboard } from './pages/AdminDashboard';
import { ManagerDashboard } from './pages/ManagerDashboard';
import { DriverDashboard } from './pages/DriverDashboard';
import { OperationsDashboard } from './pages/OperationsDashboard';
import { LogisticsMap } from './pages/LogisticsMap';
import { OptimizationConsole } from './pages/OptimizationConsole';
import { DriverRoutes } from './pages/DriverRoutes';
import { DriverActiveRoute } from './pages/DriverActiveRoute';
import { ManagerRoutes } from './pages/ManagerRoutes';
import { Unauthorized } from './pages/Unauthorized';
import { Orders } from './pages/Orders';
import { OrderDetail } from './pages/OrderDetail';
import { Drivers } from './pages/Drivers';
import { DriverDetail } from './pages/DriverDetail';
import { Vehicles } from './pages/Vehicles';
import { Warehouses } from './pages/Warehouses';
import { Customers } from './pages/Customers';
import { EtaAnalytics } from './pages/EtaAnalytics';
import { DemandAnalytics } from './pages/DemandAnalytics';
import { MaintenanceDashboard } from './pages/MaintenanceDashboard';
import { AlertsCenter } from './pages/AlertsCenter';
import { AuditLogs } from './pages/AuditLogs';
import { wsClient } from './services/websocket';



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
