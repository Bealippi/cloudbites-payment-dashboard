import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { ReconciliationRun, ReconciliationResult } from '../types';

export function useRunReconciliation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<ReconciliationRun>('/api/reconciliation/run', { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reconciliation'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['unresolved-results'] });
    },
  });
}

export function useReconciliationRuns(autoRefresh: boolean) {
  return useQuery({
    queryKey: ['reconciliation', 'runs'],
    queryFn: () => apiFetch<ReconciliationRun[]>('/api/reconciliation/runs'),
    refetchInterval: autoRefresh ? 30000 : false,
  });
}

export function useRunResults(runId: string | null) {
  return useQuery({
    queryKey: ['reconciliation', 'results', runId],
    queryFn: () => apiFetch<{ results: ReconciliationResult[]; total: number }>(
      `/api/reconciliation/runs/${runId}/results`
    ),
    enabled: !!runId,
  });
}

export function useUnresolvedResults(autoRefresh: boolean) {
  return useQuery({
    queryKey: ['unresolved-results'],
    queryFn: () => apiFetch<{ results: ReconciliationResult[]; total: number }>(
      '/api/reconciliation/results/unresolved'
    ),
    refetchInterval: autoRefresh ? 30000 : false,
  });
}

export function useResolve() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ resultId, action }: { resultId: string; action: string }) =>
      apiFetch(`/api/reconciliation/results/${resultId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ action }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reconciliation'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['unresolved-results'] });
    },
  });
}

export function useBulkResolve() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ resultIds, action }: { resultIds: string[]; action: string }) =>
      apiFetch('/api/reconciliation/results/bulk-resolve', {
        method: 'POST',
        body: JSON.stringify({ result_ids: resultIds, action }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reconciliation'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['unresolved-results'] });
    },
  });
}
