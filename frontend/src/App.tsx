import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation
} from 'react-router-dom';

import { Shell } from './components/Shell';
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
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<TerritorialPage />} />
        <Route path="/territorios" element={<TerritorialPage />} />
        <Route path="/acompanhamento" element={<OperationsPage />} />
        <Route
          path="/conceito/territorios"
          element={<LegacyRouteRedirect to="/territorios" />}
        />
        <Route
          path="/conceito/acompanhamento"
          element={<LegacyRouteRedirect to="/acompanhamento" />}
        />
        <Route path="*" element={<TerritorialPage />} />
      </Routes>
    </Shell>
  );
}

function LegacyRouteRedirect({ to }: { to: string }) {
  const location = useLocation();

  return (
    <Navigate
      replace
      to={{
        pathname: to,
        search: location.search,
        hash: location.hash
      }}
    />
  );
}
