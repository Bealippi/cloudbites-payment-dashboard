import { useState } from 'react';
import { useReconciliationRuns, useUnresolvedResults } from '../api/reconciliation';
import { RunButton } from '../components/reconciliation/RunButton';
import { MismatchesTable } from '../components/reconciliation/MismatchesTable';
import { BulkActions } from '../components/reconciliation/BulkActions';
import { RunHistory } from '../components/reconciliation/RunHistory';
import { formatDateFull } from '../lib/utils';

export function Reconciliation({ autoRefresh }: { autoRefresh: boolean }) {
  const { data: runs } = useReconciliationRuns(autoRefresh);
  const { data: unresolvedData, isLoading } = useUnresolvedResults(autoRefresh);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const results = unresolvedData?.results || [];
  const lastRun = runs?.[0];

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (results.every((r) => selectedIds.has(r.id))) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(results.map((r) => r.id)));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reconciliation Control Center</h1>
          {lastRun && (
            <p className="text-sm text-gray-500 mt-1">
              Last run: {formatDateFull(lastRun.started_at)} · {lastRun.mismatches_found} mismatches found
            </p>
          )}
        </div>
        <RunButton />
      </div>

      <BulkActions
        selectedIds={Array.from(selectedIds)}
        onClearSelection={() => setSelectedIds(new Set())}
      />

      {isLoading ? (
        <div className="bg-white rounded-xl shadow-sm border p-8 animate-pulse">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded" />
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="text-sm text-gray-500">
            {results.length} unresolved mismatch{results.length !== 1 ? 'es' : ''}
          </div>
          <MismatchesTable
            results={results}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onSelectAll={selectAll}
          />
        </>
      )}

      {runs && runs.length > 0 && <RunHistory runs={runs} />}
    </div>
  );
}
