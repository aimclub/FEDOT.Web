import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import CssBaseline from '@mui/material/CssBaseline'
import { ThemeProvider } from '@mui/material/styles'
import useMediaQuery from '@mui/material/useMediaQuery'

import { buildTheme } from '../theme'

type Mode = 'light' | 'dark'

const ThemeModeContext = createContext<{ mode: Mode; toggle: () => void }>({
  mode: 'dark',
  toggle: () => {},
})

export const useThemeMode = () => useContext(ThemeModeContext)

const STORAGE_KEY = 'fedotweb.theme'

export default function ThemeModeProvider({ children }: { children: ReactNode }) {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)')
  const [stored, setStored] = useState<Mode | null>(
    () => (localStorage.getItem(STORAGE_KEY) as Mode | null) ?? null,
  )

  const mode: Mode = stored ?? (prefersDark ? 'dark' : 'light')
  const theme = useMemo(() => buildTheme(mode), [mode])

  const value = useMemo(
    () => ({
      mode,
      toggle: () => {
        const next: Mode = mode === 'dark' ? 'light' : 'dark'
        localStorage.setItem(STORAGE_KEY, next)
        setStored(next)
      },
    }),
    [mode],
  )

  return (
    <ThemeModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeModeContext.Provider>
  )
}
