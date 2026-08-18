import { StrictMode } from 'react'
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
