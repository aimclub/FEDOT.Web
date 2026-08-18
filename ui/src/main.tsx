import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createBrowserRouter, Navigate } from 'react-router-dom'

import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/jetbrains-mono/400.css'
import '@fontsource/jetbrains-mono/700.css'
import '@xyflow/react/dist/style.css'
import './index.css'

import AppShell from './app/AppShell'
import ThemeModeProvider from './app/ThemeModeProvider'
import DatasetsPage from './pages/DatasetsPage'
import EditorPage from './pages/EditorPage'
import PipelinesPage from './pages/PipelinesPage'
import RunDetailPage from './pages/RunDetailPage'
import RunsPage from './pages/RunsPage'

// The equation-discovery mode is an optional server module, and its screens
// pull in their own charts and canvas. Loading them lazily keeps an install
// that never opens them out of the first paint entirely.
const EpdeDatasetsPage = lazy(() => import('./epde/pages/EpdeDatasetsPage'))
const EpdeRunsPage = lazy(() => import('./epde/pages/EpdeRunsPage'))
const EpdeRunDetailPage = lazy(() => import('./epde/pages/EpdeRunDetailPage'))

const lazily = (element: React.ReactNode) => <Suspense fallback={null}>{element}</Suspense>

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // The operation catalogue never changes while the server is up.
      staleTime: 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/runs" replace /> },
      { path: 'runs', element: <RunsPage /> },
      { path: 'runs/:uid', element: <RunDetailPage /> },
      { path: 'editor', element: <EditorPage /> },
      { path: 'editor/:uid', element: <EditorPage /> },
      { path: 'pipelines', element: <PipelinesPage /> },
      { path: 'datasets', element: <DatasetsPage /> },

      // EPDE mode. The nav entry only appears when the server reports the
      // module as mounted, but the routes are always registered: a bookmarked
      // link should reach a screen that explains itself rather than a blank
      // page under the SPA fallback.
      { path: 'epde', element: lazily(<Navigate to="/epde/runs" replace />) },
      { path: 'epde/runs', element: lazily(<EpdeRunsPage />) },
      { path: 'epde/runs/new', element: lazily(<EpdeRunsPage />) },
      { path: 'epde/runs/:uid', element: lazily(<EpdeRunDetailPage />) },
      { path: 'epde/datasets', element: lazily(<EpdeDatasetsPage />) },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeModeProvider>
        <RouterProvider router={router} />
      </ThemeModeProvider>
    </QueryClientProvider>
  </StrictMode>,
)
