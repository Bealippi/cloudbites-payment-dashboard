import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { DashboardStats } from '../types';

export function useDashboardStats(autoRefresh: boolean) {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiFetch<DashboardStats>('/api/dashboard/stats'),
    refetchInterval: autoRefresh ? 30000 : false,
  });
}
