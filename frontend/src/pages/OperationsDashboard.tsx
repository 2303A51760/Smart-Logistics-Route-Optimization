import React, { useEffect, useState } from 'react';
import { dashboardApi, DashboardOverviewData, OrderTrendData, DriverPerformanceData, VehicleUtilizationData } from '../services/dashboard';
import { logisticsApi } from '../services/logistics';
import { Order } from '../types';
import { StatCard } from '../components/dashboard/StatCard';
import { DashboardCard } from '../components/dashboard/DashboardCard';
import { OrderTrendChart } from '../components/dashboard/OrderTrendChart';
import { DeliveryStatusChart } from '../components/dashboard/DeliveryStatusChart';
import { DriverPerformanceTable } from '../components/dashboard/DriverPerformanceTable';
import { VehicleUtilizationGrid } from '../components/dashboard/VehicleUtilizationGrid';
import { RecentOrdersTable } from '../components/dashboard/RecentOrdersTable';
import { ActiveDriversList } from '../components/dashboard/ActiveDriversList';
import { LoadingSkeleton, ErrorState } from '../components/dashboard/FeedbackStates';

export const OperationsDashboard: React.FC = () => {
  const [overview, setOverview] = useState<DashboardOverviewData | null>(null);
  const [trends, setTrends] = useState<OrderTrendData[]>([]);
  const [driverPerf, setDriverPerf] = useState<DriverPerformanceData[]>([]);
  const [vehicleUtil, setVehicleUtil] = useState<VehicleUtilizationData | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [trendDays, setTrendDays] = useState<number>(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ov, tr, dp, vu, ordRes] = await Promise.all([
        dashboardApi.getOverview(),
        dashboardApi.getOrderTrends(trendDays),
        dashboardApi.getDriverPerformance(),
        dashboardApi.getVehicleUtilization(),
        logisticsApi.getOrders({ limit: 6 }),
      ]);
      setOverview(ov);
      setTrends(tr);
      setDriverPerf(dp);
      setVehicleUtil(vu);
      setRecentOrders(ordRes.items || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch logistics analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [trendDays]);

  if (loading && !overview) {
    return <LoadingSkeleton />;
  }

  if (error && !overview) {
    return <ErrorState message={error} onRetry={fetchDashboardData} />;
  }

  if (!overview) return null;

  return (
    <div className="space-y-6">
      {/* Dashboard Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span>📊</span> Logistics Operations Command Center
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time fleet monitoring, order throughput, driver performance, and automated dispatch KPIs.
          </p>
        </div>

        <button
          onClick={fetchDashboardData}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition flex items-center gap-2"
        >
          <span>⟳</span> Refresh Analytics
        </button>
      </div>

      {/* KPI Stats Grid - 12 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Orders"
          value={overview.orders.total}
          subtitle="All-time manifest"
          icon="📦"
          color="blue"
        />
        <StatCard
          title="Pending Orders"
          value={overview.orders.pending}
          subtitle="Awaiting assignment"
          icon="⏳"
          color="amber"
        />
        <StatCard
          title="Assigned Orders"
          value={overview.orders.assigned}
          subtitle="Dispatched to drivers"
          icon="🚚"
          color="cyan"
        />
        <StatCard
          title="Out For Delivery"
          value={overview.orders.out_for_delivery}
          subtitle="En-route in transit"
          icon="⚡"
          color="purple"
        />
        <StatCard
          title="Completed Deliveries"
          value={overview.orders.completed}
          subtitle="Successfully fulfilled"
          icon="✅"
          color="emerald"
        />
        <StatCard
          title="Failed Deliveries"
          value={overview.orders.failed}
          subtitle="Requires attention"
          icon="⚠️"
          color="rose"
        />
        <StatCard
          title="Active Drivers"
          value={overview.drivers.active}
          subtitle={`${overview.drivers.available} available now`}
          icon="🧑‍✈️"
          color="blue"
        />
        <StatCard
          title="Available Vehicles"
          value={overview.vehicles.available}
          subtitle={`${overview.vehicles.total} in total fleet`}
          icon="🚛"
          color="emerald"
        />
        <StatCard
          title="Vehicles In Maintenance"
          value={overview.vehicles.maintenance}
          subtitle="Service bay inspection"
          icon="🔧"
          color="amber"
        />
        <StatCard
          title="Total Distance"
          value={`${overview.delivery.total_distance_km.toLocaleString()} km`}
          subtitle="Fleet cumulative odometer"
          icon="🛣️"
          color="cyan"
        />
        <StatCard
          title="On-Time Delivery Rate"
          value={`${overview.delivery.on_time_rate}%`}
          subtitle="SLA benchmark"
          change="Target: >95%"
          icon="🎯"
          color="emerald"
        />
        <StatCard
          title="Average Delivery Time"
          value={`${overview.delivery.average_delivery_time} min`}
          subtitle="From hub to doorstep"
          icon="⏱️"
          color="purple"
        />
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DashboardCard
          title="Order Throughput Trends"
          subtitle="Daily volume comparison of total vs fulfilled deliveries"
          className="lg:col-span-2"
          action={
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-[11px]">
              <button
                onClick={() => setTrendDays(7)}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  trendDays === 7 ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                7 Days
              </button>
              <button
                onClick={() => setTrendDays(14)}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  trendDays === 14 ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                14 Days
              </button>
              <button
                onClick={() => setTrendDays(30)}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  trendDays === 30 ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                30 Days
              </button>
            </div>
          }
        >
          <OrderTrendChart data={trends} />
        </DashboardCard>

        <DashboardCard
          title="Delivery Status Breakdown"
          subtitle="Current distribution across fulfillment lifecycle"
        >
          <DeliveryStatusChart orders={overview.orders} />
        </DashboardCard>
      </div>

      {/* Driver Performance & Vehicle Utilization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardCard
          title="Driver Performance & Ratings"
          subtitle="Ranked by fulfillment completion rate and average turn-around"
        >
          <DriverPerformanceTable drivers={driverPerf} />
        </DashboardCard>

        <DashboardCard
          title="Fleet Utilization & Capacity"
          subtitle="Real-time vehicle status and cargo load occupancy"
        >
          {vehicleUtil && <VehicleUtilizationGrid data={vehicleUtil} />}
        </DashboardCard>
      </div>

      {/* Operational Feeds: Recent Orders & Active Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DashboardCard
          title="Recent Delivery Orders"
          subtitle="Latest client orders dispatched across logistics hubs"
          className="lg:col-span-2"
        >
          <RecentOrdersTable orders={recentOrders} />
        </DashboardCard>

        <DashboardCard
          title="Active Drivers on Duty"
          subtitle="Field personnel currently available or en-route"
        >
          <ActiveDriversList drivers={driverPerf} />
        </DashboardCard>
      </div>
    </div>
  );
};
