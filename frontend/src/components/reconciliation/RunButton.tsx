import { useRunReconciliation } from '../../api/reconciliation';

export function RunButton() {
  const runRecon = useRunReconciliation();

  return (
    <button
      onClick={() => runRecon.mutate()}
      disabled={runRecon.isPending}
      className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
    >
      {runRecon.isPending ? (
        <>
          <span className="animate-spin">⟳</span> Running...
        </>
      ) : (
        <>▶ Run Reconciliation Now</>
      )}
    </button>
  );
}
