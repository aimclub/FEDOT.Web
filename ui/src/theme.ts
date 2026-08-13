import { createTheme, type Theme } from '@mui/material/styles'

/**
 * Colours used to distinguish operation groups on the pipeline canvas.
 *
 * They double as the legend, so they need to stay distinguishable in both
 * themes and reasonably far apart for viewers with colour vision deficiency.
 */
export const GROUP_COLORS: Record<string, string> = {
  source: '#7e57c2',
  preprocessing: '#26a69a',
  feature_engineering: '#29b6f6',
  ts_transform: '#ab47bc',
  ts_model: '#ec407a',
  linear: '#42a5f5',
  non_linear: '#5c6bc0',
  tree: '#66bb6a',
  ensemble: '#ffa726',
  deep: '#ef5350',
  model: '#8d6e63',
  data_operation: '#78909c',
}

export const groupColor = (group?: string): string =>
  (group && GROUP_COLORS[group]) || GROUP_COLORS.model

const shared = {
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: '"Inter", "Segoe UI", system-ui, sans-serif',
    h1: { fontSize: '1.6rem', fontWeight: 650, letterSpacing: '-0.02em' },
    h2: { fontSize: '1.25rem', fontWeight: 650, letterSpacing: '-0.015em' },
    h3: { fontSize: '1.05rem', fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    button: { textTransform: 'none' as const, fontWeight: 600 },
  },
}

const componentOverrides = (theme: Theme) => ({
  MuiCssBaseline: {
    styleOverrides: {
      '*::-webkit-scrollbar': { width: 10, height: 10 },
      '*::-webkit-scrollbar-thumb': {
        backgroundColor: theme.palette.divider,
        borderRadius: 8,
        border: `2px solid ${theme.palette.background.default}`,
      },
      code: { fontFamily: '"JetBrains Mono", ui-monospace, monospace', fontSize: '0.85em' },
    },
  },
  MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
  MuiTooltip: {
    styleOverrides: {
      tooltip: { fontSize: '0.78rem', lineHeight: 1.45, maxWidth: 340 },
    },
  },
  MuiChip: { styleOverrides: { root: { fontWeight: 500 } } },
})

export const buildTheme = (mode: 'light' | 'dark'): Theme => {
  const base = createTheme({
    ...shared,
    palette:
      mode === 'dark'
        ? {
            mode,
            primary: { main: '#5eead4' },
            secondary: { main: '#a78bfa' },
            background: { default: '#0f1419', paper: '#161c23' },
            divider: 'rgba(148, 163, 184, 0.22)',
          }
        : {
            mode,
            primary: { main: '#0f766e' },
            secondary: { main: '#6d28d9' },
            background: { default: '#f4f6f8', paper: '#ffffff' },
            divider: 'rgba(15, 23, 42, 0.12)',
          },
  })

  return createTheme(base, { components: componentOverrides(base) })
}
