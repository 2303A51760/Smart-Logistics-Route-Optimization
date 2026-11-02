import { api } from './api';
import {
  AIOperationsSummary,
  OrderPriorityItem,
  DispatchRecommendationItem,
  RouteReoptimizationOpportunity,
  DelayRiskItem,
} from '../types/ai';

export const aiApi = {
  async getOperationsSummary(): Promise<AIOperationsSummary> {
    const res = await api.get<AIOperationsSummary>('/ai/operations-summary');
    return res.data;
  },

  async listOrderPriorities(priority?: string, limit = 50): Promise<{ total: number; orders: OrderPriorityItem[] }> {
    const res = await api.get<{ total: number; orders: OrderPriorityItem[] }>('/ai/order-priority', {
      params: { priority, limit },
    });
    return res.data;
  },

  async getOrderPriority(orderId: string): Promise<OrderPriorityItem> {
    const res = await api.get<OrderPriorityItem>(`/ai/order-priority/${orderId}`);
    return res.data;
  },

  async getDispatchRecommendations(orderId?: string, limit = 10): Promise<{ recommendations: DispatchRecommendationItem[]; total: number }> {
    const res = await api.get<{ recommendations: DispatchRecommendationItem[]; total: number }>('/ai/dispatch/recommendations', {
      params: { order_id: orderId, limit },
    });
    return res.data;
  },

  async getOrderDelayRisk(orderId: string): Promise<DelayRiskItem> {
    const res = await api.get<DelayRiskItem>(`/ai/delay-risk/order/${orderId}`);
    return res.data;
  },

  async evaluateRouteReoptimization(routeId: string, triggerReason?: string): Promise<RouteReoptimizationOpportunity> {
    const res = await api.post<RouteReoptimizationOpportunity>(`/ai/routes/${routeId}/reoptimize`, {
      trigger_reason: triggerReason || 'Operator manual evaluation',
    });
    return res.data;
  },

  async getDemandForecast(horizon = 7, warehouseId?: string): Promise<any> {
    const res = await api.get('/ai/demand-forecast', {
      params: { horizon, warehouse_id: warehouseId },
    });
    return res.data;
  },
};
