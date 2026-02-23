import { useState } from 'react';
import { useTransaction, useLiveStatus, useReconcileTransaction } from '../../api/transactions';
import { useResolve } from '../../api/reconciliation';
import { StatusBadge } from './StatusBadge';
import { MismatchIndicator } from './MismatchIndicator';
import { formatCurrency, formatDateFull, cn } from '../../lib/utils';

export function TransactionDetail({
  transactionId,
  onClose,
}: {
  transactionId: string;
  onClose: () => void;
}) {
  const { data: txn, isLoading } = useTransaction(transactionId);
  const { data: liveStatus } = useLiveStatus(transactionId);
  const resolve = useResolve();
  const reconcile = useReconcileTransaction();
  const [showRaw, setShowRaw] = useState(false);

  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex">
        <div className="absolute inset-0 bg-black/30" onClick={onClose} />
        <div className="ml-auto w-[520px] bg-white shadow-2xl h-full overflow-auto p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-2/3" />
            <div className="h-4 bg-gray-200 rounded w-1/3" />
            <div className="h-32 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (!txn) return null;

  const unresolvedResult = txn.reconciliation_history?.find((r) => !r.resolved);

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="ml-auto w-[520px] bg-white shadow-2xl h-full overflow-auto relative">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Transaction Detail</h2>
            <p className="text-sm font-mono text-gray-500">{txn.id}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">
            &times;
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Mismatch alert banner */}
          {liveStatus?.has_mismatch && (
            <div className={cn(
              'rounded-lg p-4',
              liveStatus.mismatch_type === 'CRITICAL_STATUS_MISMATCH' || liveStatus.mismatch_type === 'MISSING_AT_PROCESSOR'
                ? 'bg-red-50 border border-red-200'
                : liveStatus.mismatch_type === 'MISSED_WEBHOOK' || liveStatus.mismatch_type === 'UNTRACKED_REFUND'
                ? 'bg-orange-50 border border-orange-200'
                : 'bg-yellow-50 border border-yellow-200'
            )}>
              <p className="font-bold text-sm">
                {liveStatus.mismatch_type?.replace(/_/g, ' ')}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Internal status does not match processor status. Live query confirmed divergence.
              </p>
            </div>
          )}

          {/* Info grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Merchant</p>
              <p className="text-sm font-medium">{txn.merchant_name}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Order</p>
              <p className="text-sm font-medium">{txn.order_id}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Amount</p>
              <p className="text-sm font-bold">{formatCurrency(txn.amount, txn.currency)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Payment Method</p>
              <p className="text-sm font-medium">{txn.payment_method}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Processor</p>
              <p className="text-sm font-medium">{txn.processor_name}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Country</p>
              <p className="text-sm font-medium">{txn.country}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Created</p>
              <p className="text-sm">{formatDateFull(txn.created_at)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Processor ID</p>
              <p className="text-sm font-mono text-xs">{txn.processor_transaction_id}</p>
            </div>
          </div>

          {/* Side-by-side status comparison */}
          <div>
            <h3 className="text-sm font-semibold mb-3 text-gray-700">Status Comparison</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-xs text-gray-500 mb-2">CloudBites (Internal)</p>
                <StatusBadge status={txn.internal_status} />
                <p className="text-xs text-gray-500 mt-2">{txn.internal_sub_status}</p>
              </div>
              <div className={cn(
                'rounded-lg p-4 border',
                liveStatus?.has_mismatch
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              )}>
                <p className="text-xs text-gray-500 mb-2">Processor (Live)</p>
                {liveStatus ? (
                  <>
                    <StatusBadge status={liveStatus.normalized_status} />
                    <p className="text-xs text-gray-500 mt-2 font-mono">
                      Raw: {liveStatus.processor_raw_status}
                    </p>
                  </>
                ) : (
                  <span className="text-sm text-gray-400">Loading...</span>
                )}
              </div>
            </div>
          </div>

          {/* Raw processor response */}
          <div>
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
            >
              {showRaw ? '▼' : '▶'} Raw Processor Response
            </button>
            {showRaw && liveStatus?.raw_response && (
              <pre className="mt-2 bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-auto max-h-64 font-mono">
                {JSON.stringify(liveStatus.raw_response, null, 2)}
              </pre>
            )}
          </div>

          {/* Reconciliation History (audit trail) */}
          {txn.reconciliation_history && txn.reconciliation_history.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 text-gray-700">Reconciliation History</h3>
              <div className="space-y-3">
                {txn.reconciliation_history.map((r) => (
                  <div
                    key={r.id}
                    className={cn(
                      'border rounded-lg p-3 text-sm',
                      r.resolved ? 'border-green-200 bg-green-50' : 'border-gray-200'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <MismatchIndicator severity={r.severity} type={r.mismatch_type} />
                      <span className="text-xs text-gray-500">{formatDateFull(r.created_at)}</span>
                    </div>
                    <div className="mt-2 text-xs text-gray-600">
                      Internal: {r.internal_status} → Processor: {r.processor_normalized_status}
                      {r.resolved && (
                        <span className="ml-2 text-green-700 font-medium">
                          Resolved ({r.resolution_action}) at {formatDateFull(r.resolved_at!)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reconcile button — fetches live from processor and updates internal status */}
          {liveStatus?.has_mismatch && (
            <div className="border-t border-gray-200 pt-4 space-y-2">
              <h3 className="text-sm font-semibold text-gray-700">Quick Reconcile</h3>
              <button
                onClick={() => reconcile.mutate(transactionId)}
                disabled={reconcile.isPending}
                className="w-full bg-green-600 text-white py-2.5 px-4 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {reconcile.isPending ? (
                  <><span className="animate-spin">⟳</span> Reconciling...</>
                ) : (
                  <>Reconcile (Accept Processor: {liveStatus.normalized_status})</>
                )}
              </button>
              {reconcile.isSuccess && (
                <p className="text-xs text-green-700 font-medium">
                  Updated: {(reconcile.data as any)?.previous_status} → {(reconcile.data as any)?.new_status}
                </p>
              )}
            </div>
          )}

          {/* Resolve buttons (for existing reconciliation results) */}
          {unresolvedResult && (
            <div className="border-t border-gray-200 pt-4 space-y-2">
              <h3 className="text-sm font-semibold text-gray-700">Resolve Mismatch Record</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => resolve.mutate({ resultId: unresolvedResult.id, action: 'ACCEPT_PROCESSOR' })}
                  disabled={resolve.isPending}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  Accept Processor
                </button>
                <button
                  onClick={() => resolve.mutate({ resultId: unresolvedResult.id, action: 'ACCEPT_INTERNAL' })}
                  disabled={resolve.isPending}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50 border"
                >
                  Keep Internal
                </button>
                <button
                  onClick={() => resolve.mutate({ resultId: unresolvedResult.id, action: 'IGNORED' })}
                  disabled={resolve.isPending}
                  className="bg-gray-100 text-gray-500 py-2 px-4 rounded-lg text-sm hover:bg-gray-200 disabled:opacity-50 border"
                >
                  Ignore
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
