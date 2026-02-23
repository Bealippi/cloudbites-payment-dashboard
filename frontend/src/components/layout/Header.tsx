export function Header({
  autoRefresh,
  onToggleRefresh,
}: {
  autoRefresh: boolean;
  onToggleRefresh: () => void;
}) {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
      <div />
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">Auto-refresh</span>
        <button
          onClick={onToggleRefresh}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            autoRefresh ? 'bg-green-500' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              autoRefresh ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
        {autoRefresh && (
          <span className="text-xs text-green-600 font-medium">ON (30s)</span>
        )}
      </div>
    </header>
  );
}
