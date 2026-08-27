import { api } from './api';
import {
  AuditLog,
  AuditLogListResponse,
  AuditLogSummary,
  AuditLogFilterParams,
} from '../types';

export const auditApi = {
  async listLogs(params?: AuditLogFilterParams): Promise<AuditLogListResponse> {
    const res = await api.get<AuditLogListResponse>('/audit-logs', { params });
    return res.data;
  },

  async getSummary(): Promise<AuditLogSummary> {
    const res = await api.get<AuditLogSummary>('/audit-logs/summary');
    return res.data;
  },

  async getLogById(id: string): Promise<AuditLog> {
    const res = await api.get<AuditLog>(`/audit-logs/${id}`);
    return res.data;
  },
};
