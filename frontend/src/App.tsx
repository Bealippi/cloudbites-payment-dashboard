import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Transactions } from './pages/Transactions';
import { Reconciliation } from './pages/Reconciliation';
import { useDashboardStats } from './api/dashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 10000, retry: 1 },
  },
});

function AppContent() {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const { data: stats } = useDashboardStats(autoRefresh);
  const mismatchCount = stats?.total_mismatches ?? 0;

  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={
            <Layout
              autoRefresh={autoRefresh}
              onToggleRefresh={() => setAutoRefresh((p) => !p)}
              mismatchCount={mismatchCount}
            />
          }
        >
          <Route index element={<Dashboard autoRefresh={autoRefresh} />} />
          <Route path="/transactions" element={<Transactions autoRefresh={autoRefresh} />} />
          <Route path="/reconciliation" element={<Reconciliation autoRefresh={autoRefresh} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
