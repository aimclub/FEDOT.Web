import { NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import AppBar from '@mui/material/AppBar'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import Stack from '@mui/material/Stack'
import Toolbar from '@mui/material/Toolbar'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import AccountTreeRoundedIcon from '@mui/icons-material/AccountTreeRounded'
import FunctionsRoundedIcon from '@mui/icons-material/FunctionsRounded'
import DarkModeRoundedIcon from '@mui/icons-material/DarkModeRounded'
import LightModeRoundedIcon from '@mui/icons-material/LightModeRounded'
import MenuBookRoundedIcon from '@mui/icons-material/MenuBookRounded'
import PlayCircleRoundedIcon from '@mui/icons-material/PlayCircleRounded'
import SchemaRoundedIcon from '@mui/icons-material/SchemaRounded'
import StorageRoundedIcon from '@mui/icons-material/StorageRounded'

import { api } from '../api/client'
import { useThemeMode } from './ThemeModeProvider'

const NAV = [
  { to: '/runs', label: 'Runs', icon: <PlayCircleRoundedIcon fontSize="small" /> },
  { to: '/editor', label: 'Pipeline editor', icon: <SchemaRoundedIcon fontSize="small" /> },
  { to: '/pipelines', label: 'Saved pipelines', icon: <AccountTreeRoundedIcon fontSize="small" /> },
  { to: '/datasets', label: 'Datasets', icon: <StorageRoundedIcon fontSize="small" /> },
]

/**
 * Shown only when the server reports the optional EPDE module as mounted.
 * Offering the screens otherwise would mean every request from them 404s, which
 * looks like a broken application rather than an absent module.
 */
const EPDE_NAV = [
  { to: '/epde/runs', label: 'Equations', icon: <FunctionsRoundedIcon fontSize="small" /> },
]

export default function AppShell() {
  const theme = useTheme()
  const { mode, toggle } = useThemeMode()
  const { data: capabilities } = useQuery({
    queryKey: ['capabilities'],
    queryFn: api.capabilities,
    staleTime: Infinity,
  })

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar
        position="static"
        elevation={0}
        color="transparent"
        sx={{
          borderBottom: '1px solid',
          borderColor: 'divider',
          bgcolor: alpha(theme.palette.background.paper, 0.85),
          backdropFilter: 'blur(8px)',
        }}
      >
        <Toolbar variant="dense" sx={{ gap: 2, minHeight: 54 }}>
          <Typography variant="h1" sx={{ fontSize: '1.05rem', mr: 1 }}>
            FEDOT<Box component="span" sx={{ color: 'primary.main' }}>.Web</Box>
          </Typography>

          <Stack direction="row" spacing={0.5}>
            {[...NAV, ...(capabilities?.epde_module ? EPDE_NAV : [])].map((item) => (
              <Box
                key={item.to}
                component={NavLink}
                to={item.to}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.75,
                  px: 1.4,
                  py: 0.7,
                  borderRadius: 1.5,
                  fontSize: '0.86rem',
                  fontWeight: 600,
                  textDecoration: 'none',
                  color: 'text.secondary',
                  '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.08) },
                  '&.active': {
                    color: 'primary.main',
                    bgcolor: alpha(theme.palette.primary.main, 0.13),
                  },
                }}
              >
                {item.icon}
                {item.label}
              </Box>
            ))}
          </Stack>

          <Box sx={{ flexGrow: 1 }} />

          {capabilities && (
            <Stack direction="row" spacing={0.75} alignItems="center">
              {capabilities.fedot_version && (
                <Tooltip title="Version of the FEDOT framework this server drives">
                  <Chip size="small" variant="outlined" label={`FEDOT ${capabilities.fedot_version}`} />
                </Tooltip>
              )}
              {capabilities.golem_version && (
                <Tooltip title="Version of the GOLEM optimiser used for evolution">
                  <Chip size="small" variant="outlined" label={`GOLEM ${capabilities.golem_version}`} />
                </Tooltip>
              )}
              {capabilities.epde_module && (
                <Tooltip title="The equation-discovery module is mounted. EPDE does not use GOLEM; it runs its own evolutionary search.">
                  <Chip size="small" variant="outlined" color="secondary" label="EPDE" />
                </Tooltip>
              )}
            </Stack>
          )}

          <Tooltip title="API reference">
            <IconButton size="small" component="a" href="/docs" target="_blank" rel="noreferrer">
              <MenuBookRoundedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={mode === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}>
            <IconButton size="small" onClick={toggle}>
              {mode === 'dark' ? (
                <LightModeRoundedIcon fontSize="small" />
              ) : (
                <DarkModeRoundedIcon fontSize="small" />
              )}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Box sx={{ flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
        <Outlet />
      </Box>
    </Box>
  )
}
