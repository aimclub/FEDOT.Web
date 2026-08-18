import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Grid from '@mui/material/Grid'
import IconButton from '@mui/material/IconButton'
import MenuItem from '@mui/material/MenuItem'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded'

import { epdeApi } from '../api/client'
import RunConfigForm from '../runs/RunConfigForm'
import type { EpdeRunConfig, RunStatus } from '../api/types'

const STATUS_COLOR: Record<RunStatus, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  running: 'info',
  finished: 'success',
  failed: 'error',
  cancelled: 'warning',
}

export default function EpdeRunsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const [datasetUid, setDatasetUid] = useState<string>(params.get('dataset') ?? '')
  const [startError, setStartError] = useState<string | null>(null)

  const { data: capabilities } = useQuery({
    queryKey: ['epde-capabilities'],
    queryFn: epdeApi.capabilities,
    staleTime: Infinity,
  })
  const { data: datasets } = useQuery({ queryKey: ['epde-datasets'], queryFn: epdeApi.datasets })
  const { data: runs, isLoading } = useQuery({
    queryKey: ['epde-runs'],
    queryFn: epdeApi.runs,
    refetchInterval: (query) =>
      (query.state.data ?? []).some((run) => run.status === 'running' || run.status === 'pending')
        ? 4000
        : false,
  })

  const dataset = useMemo(
    () => datasets?.find((entry) => entry.uid === datasetUid) ?? datasets?.[0] ?? null,
    [datasets, datasetUid],
  )

  // A built-in field carries the equation it satisfies, which is what makes a
  // run judgeable rather than merely interesting.
  const sample = useMemo(() => {
    const origin = dataset?.origin ?? ''
    if (!origin.startsWith('sample:')) return null
    const id = origin.slice('sample:'.length)
    return capabilities?.samples.find((entry) => entry.id === id) ?? null
  }, [dataset, capabilities])

  const start = useMutation({
    mutationFn: ({ config, name }: { config: EpdeRunConfig; name?: string }) =>
      epdeApi.startRun(config, name),
    onSuccess: (record) => {
      setStartError(null)
      queryClient.invalidateQueries({ queryKey: ['epde-runs'] })
      navigate(`/epde/runs/${record.uid}`)
    },
    onError: (error: Error) => setStartError(error.message),
  })

  const remove = useMutation({
    mutationFn: (uid: string) => epdeApi.deleteRun(uid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['epde-runs'] }),
  })

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', p: 3 }}>
      <Typography variant="h1" sx={{ fontSize: '1.25rem', mb: 2 }}>
        Equation discovery
      </Typography>

      {capabilities && !capabilities.epde_available && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {capabilities.epde_error}
        </Alert>
      )}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h3" sx={{ mb: 1.5 }}>
              New search
            </Typography>

            {(datasets?.length ?? 0) === 0 ? (
              <Stack spacing={1.5}>
                <Typography variant="body2" color="text.secondary">
                  A search needs a field to work on.
                </Typography>
                <Button size="small" variant="outlined" onClick={() => navigate('/epde/datasets')}>
                  Add a field
                </Button>
              </Stack>
            ) : (
              <Stack spacing={2}>
                <TextField
                  size="small"
                  select
                  fullWidth
                  label="Field"
                  value={dataset?.uid ?? ''}
                  onChange={(event) => setDatasetUid(event.target.value)}
                >
                  {datasets?.map((entry) => (
                    <MenuItem key={entry.uid} value={entry.uid}>
                      {entry.name} · {entry.shape.join(' × ')}
                    </MenuItem>
                  ))}
                </TextField>

                {startError && (
                  <Alert severity="error" onClose={() => setStartError(null)}>
                    {startError}
                  </Alert>
                )}

                {dataset && capabilities && (
                  <RunConfigForm
                    dataset={dataset}
                    capabilities={capabilities}
                    sample={sample}
                    busy={start.isPending}
                    onStart={(config, name) => start.mutate({ config, name })}
                  />
                )}
              </Stack>
            )}
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, lg: 7 }}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h3" sx={{ mb: 1.5 }}>
              Runs
            </Typography>

            {isLoading && (
              <Stack alignItems="center" sx={{ py: 4 }}>
                <CircularProgress size={22} />
              </Stack>
            )}

            {runs?.length === 0 && (
              <Typography variant="body2" color="text.disabled">
                No search has been started yet.
              </Typography>
            )}

            <Stack spacing={1}>
              {runs?.map((run) => (
                <Paper
                  key={run.uid}
                  variant="outlined"
                  sx={{ p: 1.5, cursor: 'pointer' }}
                  onClick={() => navigate(`/epde/runs/${run.uid}`)}
                >
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <Box sx={{ minWidth: 0, flexGrow: 1 }}>
                      <Typography variant="subtitle2" noWrap>
                        {run.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(run.created_at).toLocaleString()}
                        {typeof run.config?.epochs === 'number' && ` · ${run.config.epochs} generations`}
                        {typeof run.config?.population_size === 'number' &&
                          ` · population ${run.config.population_size}`}
                      </Typography>
                    </Box>
                    <Chip size="small" color={STATUS_COLOR[run.status] ?? 'default'} label={run.status} />
                    <Tooltip title="Delete this run">
                      <span>
                        <IconButton
                          size="small"
                          disabled={run.status === 'running'}
                          onClick={(event) => {
                            event.stopPropagation()
                            remove.mutate(run.uid)
                          }}
                        >
                          <DeleteRoundedIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </Stack>
                  {run.error && (
                    <Typography variant="caption" color="error.main">
                      {run.error}
                    </Typography>
                  )}
                </Paper>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
