import { StatusBadge } from './StatusBadge';
import { MismatchIndicator } from './MismatchIndicator';
import { formatCurrency, formatDate, cn, SEVERITY_BORDER } from '../../lib/utils';
import type { Transaction } from '../../types';

export function TransactionsTable({
  transactions,
  onSelect,
  page,
  totalPages,
  onPageChange,
}: {
  transactions: Transaction[];
  onSelect: (txn: Transaction) => void;
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Merchant</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Amount</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Internal Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Processor</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Proc. Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Mismatch</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => (
              <tr
                key={txn.id}
                onClick={() => onSelect(txn)}
                className={cn(
                  'border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors',
                  txn.has_mismatch && txn.mismatch_severity
                    ? SEVERITY_BORDER[txn.mismatch_severity]
                    : ''
                )}
              >
                <td className="px-4 py-3">
                  <span className="text-sm font-mono text-blue-600">{txn.id.slice(0, 12)}</span>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-gray-900">{txn.merchant_name}</p>
                  <p className="text-xs text-gray-500">{txn.order_id}</p>
                </td>
                <td className="px-4 py-3 text-sm font-medium">
                  {formatCurrency(txn.amount, txn.currency)}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={txn.internal_status} />
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{txn.processor_name}</td>
                <td className="px-4 py-3 text-sm font-mono text-gray-600">
                  {txn.processor_status || '-'}
                </td>
                <td className="px-4 py-3">
                  {txn.has_mismatch && txn.mismatch_severity && txn.mismatch_type ? (
                    <MismatchIndicator severity={txn.mismatch_severity} type={txn.mismatch_type} />
                  ) : (
                    <span className="text-xs text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {formatDate(txn.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1.5 text-sm border rounded-md disabled:opacity-50 hover:bg-white"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-3 py-1.5 text-sm border rounded-md disabled:opacity-50 hover:bg-white"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
