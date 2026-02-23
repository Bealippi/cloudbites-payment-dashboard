import { useNavigate } from 'react-router-dom';
import { MismatchIndicator } from '../transactions/MismatchIndicator';
import { formatCurrency } from '../../lib/utils';
import { useResolve } from '../../api/reconciliation';
import type { ReconciliationResult } from '../../types';

export function RecentMismatches({ mismatches }: { mismatches: ReconciliationResult[] }) {
  const navigate = useNavigate();
  const resolve = useResolve();

  if (mismatches.length === 0) {
    return (
      <div>
        <h2 className="text-lg font-semibold mb-4">Recent Mismatches</h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-gray-500">
          No mismatches detected. Run reconciliation to check.
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Recent Mismatches</h2>
        <button
          onClick={() => navigate('/reconciliation')}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View all →
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Transaction</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Mismatch</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Amount</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Action</th>
            </tr>
          </thead>
          <tbody>
            {mismatches.map((m) => (
              <tr key={m.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3">
                  <p className="text-sm font-mono text-gray-900">{m.transaction_id.slice(0, 12)}...</p>
                  <p className="text-xs text-gray-500">{m.processor_name}</p>
                </td>
                <td className="px-4 py-3">
                  <MismatchIndicator severity={m.severity} type={m.mismatch_type} />
                </td>
                <td className="px-4 py-3 text-sm">
                  {m.amount && m.currency ? formatCurrency(m.amount, m.currency) : '-'}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => resolve.mutate({ resultId: m.id, action: 'ACCEPT_PROCESSOR' })}
                    disabled={resolve.isPending}
                    className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
                  >
                    Accept Processor
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
