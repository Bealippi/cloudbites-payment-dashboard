import { useDashboardStats } from '../api/dashboard';
import { SummaryCards } from '../components/dashboard/SummaryCards';
import { ProcessorHealth } from '../components/dashboard/ProcessorHealth';
import { RecentMismatches } from '../components/dashboard/RecentMismatches';

export function Dashboard({ autoRefresh }: { autoRefresh: boolean }) {
  const { data: stats, isLoading } = useDashboardStats(autoRefresh);

  if (isLoading || !stats) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-24 mb-3" />
              <div className="h-8 bg-gray-200 rounded w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <SummaryCards stats={stats} />
      <ProcessorHealth processors={stats.processor_breakdown} />
      <RecentMismatches mismatches={stats.recent_mismatches} />
    </div>
  );
}
