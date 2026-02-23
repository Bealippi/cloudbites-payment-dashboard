import { cn } from '../../lib/utils';
import type { TransactionFilters } from '../../types';

const STATUSES = ['All', 'SUCCEEDED', 'PENDING', 'DECLINED', 'REFUNDED', 'AUTHORIZED', 'ERROR', 'EXPIRED', 'CANCELED'];
const PROCESSORS = ['PayFlow', 'StripeConnect', 'LatamPay'];

export function FilterBar({
  filters,
  onFilterChange,
}: {
  filters: TransactionFilters;
  onFilterChange: (f: Partial<TransactionFilters>) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="relative">
        <input
          type="text"
          placeholder="Search by ID, order, merchant, or processor ID..."
          value={filters.search || ''}
          onChange={(e) => onFilterChange({ search: e.target.value, page: 1 })}
          className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-xl bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <svg className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex gap-1 flex-wrap">
          {STATUSES.map((s) => {
            const active = s === 'All' ? !filters.status : filters.status === s;
            return (
              <button
                key={s}
                onClick={() => onFilterChange({ status: s === 'All' ? undefined : s, page: 1 })}
                className={cn(
                  'px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
                  active
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                {s}
              </button>
            );
          })}
        </div>

        <div className="h-6 w-px bg-gray-300" />

        <div className="flex gap-2">
          {PROCESSORS.map((p) => (
            <button
              key={p}
              onClick={() =>
                onFilterChange({
                  processor: filters.processor === p ? undefined : p,
                  page: 1,
                })
              }
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                filters.processor === p
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              )}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="h-6 w-px bg-gray-300" />

        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">From</label>
          <input
            type="date"
            value={filters.dateFrom || ''}
            onChange={(e) => onFilterChange({ dateFrom: e.target.value || undefined, page: 1 })}
            className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <label className="text-xs text-gray-500">To</label>
          <input
            type="date"
            value={filters.dateTo || ''}
            onChange={(e) => onFilterChange({ dateTo: e.target.value || undefined, page: 1 })}
            className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {(filters.dateFrom || filters.dateTo) && (
            <button
              onClick={() => onFilterChange({ dateFrom: undefined, dateTo: undefined, page: 1 })}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
