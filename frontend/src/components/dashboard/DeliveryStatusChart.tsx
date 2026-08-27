import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import { OrderMetrics } from '../../types';

export interface DeliveryStatusChartProps {
  orders: OrderMetrics;
}

export const DeliveryStatusChart: React.FC<DeliveryStatusChartProps> = ({ orders }) => {
  const data = [
    { name: 'Delivered', value: orders.completed || 0, color: '#10b981' },
    { name: 'Out For Delivery', value: orders.out_for_delivery || 0, color: '#0ea5e9' },
    { name: 'Assigned', value: orders.assigned || 0, color: '#6366f1' },
    { name: 'Pending', value: orders.pending || 0, color: '#f59e0b' },
    { name: 'Failed', value: orders.failed || 0, color: '#f43f5e' },
    { name: 'Cancelled', value: orders.cancelled || 0, color: '#64748b' },
  ].filter((d) => d.value > 0);

  // Fallback if zero items
  const chartData = data.length > 0 ? data : [{ name: 'No Orders', value: 1, color: '#334155' }];

  return (
    <div className="w-full h-72 flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="45%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={4}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '0.75rem',
              color: '#f8fafc',
              fontSize: '12px',
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => <span className="text-xs text-slate-300 ml-1">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
