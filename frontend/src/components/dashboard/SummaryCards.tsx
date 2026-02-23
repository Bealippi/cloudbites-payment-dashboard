import type { DashboardStats } from '../../types';

export function SummaryCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    { label: 'Total Transactions', value: stats.total_transactions, color: 'text-gray-900' },
    { label: 'Success Rate', value: `${stats.success_rate}%`, color: 'text-green-600' },
    {
      label: 'Mismatches',
      value: stats.total_mismatches,
      color: stats.total_mismatches > 0 ? 'text-red-600' : 'text-gray-900',
      alert: stats.total_mismatches > 0,
    },
    { label: 'Pending Txns', value: stats.pending_transactions, color: 'text-yellow-600' },
  ];

  return (
    <div className="grid grid-cols-4 gap-6">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`bg-white rounded-xl shadow-sm border p-6 ${
            card.alert ? 'border-red-200 bg-red-50' : 'border-gray-200'
          }`}
        >
          <p className="text-sm text-gray-500 font-medium">{card.label}</p>
          <p className={`text-3xl font-bold mt-2 ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}
