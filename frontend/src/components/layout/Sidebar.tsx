import { NavLink } from 'react-router-dom';
import { cn } from '../../lib/utils';

const links = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/transactions', label: 'Transactions', icon: '💳' },
  { to: '/reconciliation', label: 'Reconciliation', icon: '🔄' },
];

export function Sidebar({ mismatchCount }: { mismatchCount: number }) {
  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold">CloudBites</h1>
        <p className="text-sm text-gray-400 mt-1">Payment Visibility</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )
            }
          >
            <span>{link.icon}</span>
            <span>{link.label}</span>
            {link.to === '/reconciliation' && mismatchCount > 0 && (
              <span className="ml-auto bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                {mismatchCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
