import { StatusBadge } from '../transactions/StatusBadge';
import { MismatchIndicator } from '../transactions/MismatchIndicator';
import { useResolve } from '../../api/reconciliation';
import { formatCurrency } from '../../lib/utils';
import { cn, SEVERITY_BORDER } from '../../lib/utils';
import type { ReconciliationResult } from '../../types';

export function MismatchesTable({
  results,
  selectedIds,
  onToggleSelect,
  onSelectAll,
}: {
  results: ReconciliationResult[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onSelectAll: () => void;
}) {
  const resolve = useResolve();
  const allSelected = results.length > 0 && results.every((r) => selectedIds.has(r.id));

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-gray-500">
        No unresolved mismatches. Run reconciliation to check for new ones.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="px-4 py-3 w-10">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onSelectAll}
                className="rounded border-gray-300"
              />
            </th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Transaction</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Internal</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Processor</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Mismatch</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Amount</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Action</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr
              key={r.id}
              className={cn(
                'border-b border-gray-100 hover:bg-gray-50',
                SEVERITY_BORDER[r.severity] || ''
              )}
            >
              <td className="px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectedIds.has(r.id)}
                  onChange={() => onToggleSelect(r.id)}
                  className="rounded border-gray-300"
                />
              </td>
              <td className="px-4 py-3">
                <p className="text-sm font-mono text-blue-600">{r.transaction_id.slice(0, 12)}</p>
                <p className="text-xs text-gray-500">{r.processor_name} · {r.merchant_name}</p>
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={r.internal_status} />
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={r.processor_normalized_status} />
                <p className="text-xs text-gray-500 mt-1 font-mono">{r.processor_raw_status}</p>
              </td>
              <td className="px-4 py-3">
                <MismatchIndicator severity={r.severity} type={r.mismatch_type} />
              </td>
              <td className="px-4 py-3 text-sm font-medium">
                {r.amount && r.currency ? formatCurrency(r.amount, r.currency) : '-'}
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1">
                  <button
                    onClick={() => resolve.mutate({ resultId: r.id, action: 'ACCEPT_PROCESSOR' })}
                    disabled={resolve.isPending}
                    className="text-xs bg-blue-600 text-white px-2.5 py-1 rounded hover:bg-blue-700 disabled:opacity-50 font-medium"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => resolve.mutate({ resultId: r.id, action: 'IGNORED' })}
                    disabled={resolve.isPending}
                    className="text-xs bg-gray-200 text-gray-700 px-2.5 py-1 rounded hover:bg-gray-300 disabled:opacity-50"
                  >
                    Ignore
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
