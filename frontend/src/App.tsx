import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom';

import { ConceptShell } from './components/ConceptShell';
import { Shell } from './components/Shell';
import { ConceptOperationsPage } from './pages/ConceptOperationsPage';
import { ConceptTerritorialPage } from './pages/ConceptTerritorialPage';
import { OperationsPage } from './pages/OperationsPage';
import { TerritorialPage } from './pages/TerritorialPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 60_000
    }
  }
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function AppRoutes() {
  const location = useLocation();
  const isConceptRoute = location.pathname.startsWith('/conceito');
  const Layout = isConceptRoute ? ConceptShell : Shell;

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<TerritorialPage />} />
        <Route path="/territorios" element={<TerritorialPage />} />
        <Route path="/acompanhamento" element={<OperationsPage />} />
        <Route path="/conceito/territorios" element={<ConceptTerritorialPage />} />
        <Route path="/conceito/acompanhamento" element={<ConceptOperationsPage />} />
        <Route path="*" element={<TerritorialPage />} />
      </Routes>
    </Layout>
  );
}
