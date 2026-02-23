import { formatDateFull } from '../../lib/utils';
import type { ReconciliationRun } from '../../types';

export function RunHistory({ runs }: { runs: ReconciliationRun[] }) {
  if (runs.length === 0) return null;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Run History</h3>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Run</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Checked</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Mismatches</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run, i) => (
              <tr key={run.id} className="border-b border-gray-100">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  Run #{runs.length - i}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {formatDateFull(run.started_at)}
                </td>
                <td className="px-4 py-3 text-sm">{run.total_checked}</td>
                <td className="px-4 py-3">
                  <span className={`text-sm font-medium ${run.mismatches_found > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {run.mismatches_found}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    run.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {run.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
