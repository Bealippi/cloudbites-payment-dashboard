import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { TransactionListResponse, Transaction, LiveStatusResponse, TransactionFilters, ReconcileResponse } from '../types';

export function useTransactions(filters: TransactionFilters, autoRefresh: boolean) {
  const params = new URLSearchParams();
  params.set('page', String(filters.page));
  params.set('limit', String(filters.limit));
  if (filters.status) params.set('status', filters.status);
  if (filters.processor) params.set('processor', filters.processor);
  if (filters.search) params.set('search', filters.search);
  if (filters.dateFrom) params.set('dateFrom', filters.dateFrom);
  if (filters.dateTo) params.set('dateTo', filters.dateTo);

  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => apiFetch<TransactionListResponse>(`/api/transactions?${params}`),
    refetchInterval: autoRefresh ? 30000 : false,
  });
}

export function useTransaction(id: string | null) {
  return useQuery({
    queryKey: ['transaction', id],
    queryFn: () => apiFetch<Transaction>(`/api/transactions/${id}`),
    enabled: !!id,
  });
}

export function useLiveStatus(id: string | null) {
  return useQuery({
    queryKey: ['live-status', id],
    queryFn: () => apiFetch<LiveStatusResponse>(`/api/transactions/${id}/live-status`),
    enabled: !!id,
  });
}

export function useReconcileTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (transactionId: string) =>
      apiFetch<ReconcileResponse>(`/api/transactions/${transactionId}/reconcile`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['transaction'] });
      qc.invalidateQueries({ queryKey: ['live-status'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
      qc.invalidateQueries({ queryKey: ['unresolved-results'] });
      qc.invalidateQueries({ queryKey: ['reconciliation'] });
    },
  });
}
