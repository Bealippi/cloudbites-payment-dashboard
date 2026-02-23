import type { ProcessorBreakdown } from '../../types';

export function ProcessorHealth({ processors }: { processors: ProcessorBreakdown[] }) {
  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Processor Health</h2>
      <div className="grid grid-cols-3 gap-6">
        {processors.map((proc) => (
          <div key={proc.name} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">{proc.name}</h3>
              <span className="text-sm text-gray-500">{proc.total} txns</span>
            </div>
            <div className="mb-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-500">Success Rate</span>
                <span className="font-medium">{proc.success_rate}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-green-500 h-2.5 rounded-full transition-all"
                  style={{ width: `${proc.success_rate}%` }}
                />
              </div>
            </div>
            {proc.mismatches > 0 && (
              <div className="flex items-center gap-2 mt-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-700">
                  {proc.mismatches} mismatches
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
