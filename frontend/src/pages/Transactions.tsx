import { useState, useCallback } from 'react';
import { useTransactions } from '../api/transactions';
import { FilterBar } from '../components/transactions/FilterBar';
import { TransactionsTable } from '../components/transactions/TransactionsTable';
import { TransactionDetail } from '../components/transactions/TransactionDetail';
import type { TransactionFilters, Transaction } from '../types';

export function Transactions({ autoRefresh }: { autoRefresh: boolean }) {
  const [filters, setFilters] = useState<TransactionFilters>({
    page: 1,
    limit: 20,
  });
  const [selectedTxn, setSelectedTxn] = useState<string | null>(null);

  const { data, isLoading } = useTransactions(filters, autoRefresh);

  const handleFilterChange = useCallback((partial: Partial<TransactionFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial }));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Transaction Explorer</h1>

      <FilterBar filters={filters} onFilterChange={handleFilterChange} />

      {isLoading ? (
        <div className="bg-white rounded-xl shadow-sm border p-8 animate-pulse">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded" />
            ))}
          </div>
        </div>
      ) : data ? (
        <>
          <div className="text-sm text-gray-500">
            Showing {data.transactions.length} of {data.total} transactions
          </div>
          <TransactionsTable
            transactions={data.transactions}
            onSelect={(txn: Transaction) => setSelectedTxn(txn.id)}
            page={data.page}
            totalPages={data.total_pages}
            onPageChange={(p) => handleFilterChange({ page: p })}
          />
        </>
      ) : null}

      {selectedTxn && (
        <TransactionDetail
          transactionId={selectedTxn}
          onClose={() => setSelectedTxn(null)}
        />
      )}
    </div>
  );
}
