import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function Layout({
  autoRefresh,
  onToggleRefresh,
  mismatchCount,
}: {
  autoRefresh: boolean;
  onToggleRefresh: () => void;
  mismatchCount: number;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar mismatchCount={mismatchCount} />
      <div className="flex-1 flex flex-col">
        <Header autoRefresh={autoRefresh} onToggleRefresh={onToggleRefresh} />
        <main className="flex-1 p-8 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
