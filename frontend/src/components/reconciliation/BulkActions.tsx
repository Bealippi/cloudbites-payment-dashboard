import { useBulkResolve } from '../../api/reconciliation';

export function BulkActions({
  selectedIds,
  onClearSelection,
}: {
  selectedIds: string[];
  onClearSelection: () => void;
}) {
  const bulkResolve = useBulkResolve();

  const handleBulkResolve = (action: string) => {
    bulkResolve.mutate(
      { resultIds: selectedIds, action },
      { onSuccess: () => onClearSelection() }
    );
  };

  if (selectedIds.length === 0) return null;

  return (
    <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
      <span className="text-sm font-medium text-blue-800">
        {selectedIds.length} selected
      </span>
      <div className="flex gap-2">
        <button
          onClick={() => handleBulkResolve('ACCEPT_PROCESSOR')}
          disabled={bulkResolve.isPending}
          className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
        >
          Accept All (Processor)
        </button>
        <button
          onClick={() => handleBulkResolve('IGNORED')}
          disabled={bulkResolve.isPending}
          className="text-xs bg-gray-500 text-white px-3 py-1.5 rounded-md hover:bg-gray-600 disabled:opacity-50 font-medium"
        >
          Ignore All
        </button>
      </div>
      <button
        onClick={onClearSelection}
        className="ml-auto text-xs text-gray-500 hover:text-gray-700"
      >
        Clear
      </button>
    </div>
  );
}
