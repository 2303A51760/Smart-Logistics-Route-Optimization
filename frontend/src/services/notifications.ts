import { api } from './api';
import {
  Notification,
  NotificationListResponse,
  NotificationSummary,
} from '../types';

export const notificationsApi = {
  async getNotifications(params?: {
    unread_only?: boolean;
    alert_type?: string;
    severity?: string;
    limit?: number;
  }): Promise<NotificationListResponse> {
    const res = await api.get<NotificationListResponse>('/notifications', { params });
    return res.data;
  },

  async getSummary(): Promise<NotificationSummary> {
    const res = await api.get<NotificationSummary>('/notifications/summary');
    return res.data;
  },

  async markAsRead(id: string): Promise<Notification> {
    const res = await api.patch<Notification>(`/notifications/${id}/read`);
    return res.data;
  },

  async markAllAsRead(): Promise<{ status: string; marked_read_count: number }> {
    const res = await api.post('/notifications/mark-all-read');
    return res.data;
  },

  async triggerAlertAudit(): Promise<{
    total_alerts_generated: number;
    alerts: Notification[];
    details: Record<string, number>;
  }> {
    const res = await api.post('/notifications/check-alerts');
    return res.data;
  },

  async dismissNotification(id: string): Promise<{ status: string; message: string }> {
    const res = await api.delete(`/notifications/${id}`);
    return res.data;
  },
};
