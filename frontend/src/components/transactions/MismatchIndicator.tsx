import { cn, SEVERITY_COLORS } from '../../lib/utils';

export function MismatchIndicator({
  severity,
  type,
}: {
  severity: string;
  type: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded text-xs font-bold',
          SEVERITY_COLORS[severity] || 'bg-gray-200 text-gray-700'
        )}
      >
        {severity}
      </span>
      <span className="text-xs text-gray-500 max-w-[160px] truncate" title={type}>
        {type.replace(/_/g, ' ')}
      </span>
    </div>
  );
}
