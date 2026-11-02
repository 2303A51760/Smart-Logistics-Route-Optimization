import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { Orders } from '../pages/Orders';
import { logisticsApi } from '../services/logistics';
import { authStorage, authApi } from '../services/auth';

describe('Orders Page Rendering & Filtering', () => {
  const mockOrdersResponse = {
    items: [
      {
        id: 'ord-001',
        order_number: 'ORD-1001',
        customer_id: 'cust-001',
        warehouse_id: 'wh-001',
        customer_name: 'Tech Hub Broadway',
        warehouse_name: 'Manhattan Fulfillment Hub',
        pickup_latitude: 40.7538,
        pickup_longitude: -74.0017,
        delivery_latitude: 40.7209,
        delivery_longitude: -74.0005,
        package_weight: 15.0,
        priority: 'HIGH' as const,
        status: 'PENDING' as const,
        created_at: '2026-11-01T10:00:00Z',
        updated_at: '2026-11-01T10:00:00Z',
      },
      {
        id: 'ord-002',
        order_number: 'ORD-1002',
        customer_id: 'cust-002',
        warehouse_id: 'wh-002',
        customer_name: 'Midtown Clinic',
        warehouse_name: 'Brooklyn Distribution',
        pickup_latitude: 40.6508,
        pickup_longitude: -74.0152,
        delivery_latitude: 40.7505,
        delivery_longitude: -73.9735,
        package_weight: 5.5,
        priority: 'URGENT' as const,
        status: 'ASSIGNED' as const,
        created_at: '2026-11-01T10:30:00Z',
        updated_at: '2026-11-01T10:30:00Z',
      },
    ],
    total: 2,
    page: 1,
    size: 10,
    total_pages: 1,
  };

  const mockManagerUser = {
    id: 'usr-mgr-002',
    name: 'Manager Bob',
    email: 'manager@example.com',
    role: 'LOGISTICS_MANAGER' as const,
    is_active: true,
    created_at: '2026-11-01T00:00:00Z',
  };

  beforeEach(() => {
    authStorage.setSession({
      access_token: 'fake-token',
      refresh_token: 'fake-refresh',
      token_type: 'bearer',
      user: mockManagerUser,
    });

    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockManagerUser);
    vi.spyOn(logisticsApi, 'getOrders').mockResolvedValue(mockOrdersResponse);
    vi.spyOn(logisticsApi, 'getCustomers').mockResolvedValue([]);
    vi.spyOn(logisticsApi, 'getWarehouses').mockResolvedValue([]);
    vi.spyOn(logisticsApi, 'getDrivers').mockResolvedValue([]);
  });

  it('renders order list with order numbers, customers, and priority badges', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Orders />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('ORD-1001')).toBeInTheDocument();
      expect(screen.getByText('ORD-1002')).toBeInTheDocument();
      expect(screen.getByText('Tech Hub Broadway')).toBeInTheDocument();
      expect(screen.getByText('Midtown Clinic')).toBeInTheDocument();
    });
  });

  it('filters orders by search term', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Orders />
        </AuthProvider>
      </BrowserRouter>
    );

    const searchInput = screen.getByPlaceholderText(/search by order # or customer/i);
    fireEvent.change(searchInput, { target: { value: 'ORD-1001' } });
    fireEvent.submit(searchInput.closest('form')!);

    await waitFor(() => {
      expect(logisticsApi.getOrders).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'ORD-1001',
        })
      );
    });
  });

  it('displays empty state when zero orders are returned', async () => {
    vi.spyOn(logisticsApi, 'getOrders').mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      size: 10,
      total_pages: 1,
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <Orders />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no orders found/i)).toBeInTheDocument();
    });
  });
});
