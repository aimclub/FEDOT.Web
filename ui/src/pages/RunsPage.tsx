import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded'
import StopRoundedIcon from '@mui/icons-material/StopRounded'

import { api } from '../api/client'
import type { RunStatus } from '../api/types'
import RunConfigForm, { defaultRunConfig } from '../runs/RunConfigForm'
import { useEditorStore } from '../pipeline/editorStore'

const STATUS_COLOR: Record<RunStatus, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  running: 'info',
  finished: 'success',
  failed: 'error',
  cancelled: 'warning',
}

export default function RunsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const editorGraph = useEditorStore((state) => state.graph)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [useEditorPipeline, setUseEditorPipeline] = useState(false)
  const [name, setName] = useState('')
  const [config, setConfig] = useState(defaultRunConfig())
  const [error, setError] = useState<string | null>(null)

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: api.runs,
    // Keep the list fresh while something is composing.
    refetchInterval: (query) =>
      (query.state.data ?? []).some((run) => run.status === 'running' || run.status === 'pending')
        ? 3000
        : false,
  })

  const start = useMutation({
    mutationFn: () =>
      api.startRun(
        {
          ...config,
          initial_pipeline: useEditorPipeline && editorGraph.nodes.length ? editorGraph : null,
        },
        name || undefined,
      ),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      setDialogOpen(false)
      navigate(`/runs/${run.uid}`)
    },
    onError: (startError: Error) => setError(startError.message),
  })

  const stop = useMutation({
    mutationFn: (uid: string) => api.stopRun(uid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['runs'] }),
    onError: (stopError: Error) => setError(stopError.message),
  })

  const remove = useMutation({
    mutationFn: (uid: string) => api.deleteRun(uid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['runs'] }),
    onError: (removeError: Error) => setError(removeError.message),
  })

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', p: 3 }}>
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
        <Box>
          <Typography variant="h1">AutoML runs</Typography>
          <Typography variant="body2" color="text.secondary">
            Configure and launch FEDOT compositions, and watch the evolution as it happens.
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="contained"
          startIcon={<PlayArrowRoundedIcon />}
          onClick={() => {
            setError(null)
            setUseEditorPipeline(false)
            setDialogOpen(true)
          }}
        >
          New run
        </Button>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {isLoading && <CircularProgress size={24} />}

      {!isLoading && runs.length === 0 && (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            No runs yet. Upload a dataset, then start a composition.
          </Typography>
        </Paper>
      )}

      {runs.length > 0 && (
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Run</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Task</TableCell>
                <TableCell>Metrics</TableCell>
                <TableCell>Started</TableCell>
                <TableCell align="right" />
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.map((run) => (
                <TableRow
                  key={run.uid}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/runs/${run.uid}`)}
                >
                  <TableCell>
                    <Typography variant="body2">{run.name}</Typography>
                    {run.error && (
                      <Typography variant="caption" color="error" noWrap sx={{ maxWidth: 320, display: 'block' }}>
                        {run.error}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip size="small" color={STATUS_COLOR[run.status]} label={run.status} />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">{String(run.config?.problem ?? '—')}</Typography>
                  </TableCell>
                  <TableCell>
                    {run.metrics ? (
                      <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                        {Object.entries(run.metrics).map(([metric, score]) => (
                          <Chip
                            key={metric}
                            size="small"
                            variant="outlined"
                            label={`${metric} ${score}`}
                            sx={{ height: 19, fontSize: '0.68rem' }}
                          />
                        ))}
                      </Stack>
                    ) : (
                      <Typography variant="caption" color="text.disabled">
                        —
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right" onClick={(event) => event.stopPropagation()}>
                    {(run.status === 'running' || run.status === 'pending') && (
                      <Tooltip title="Stop this run">
                        <IconButton size="small" onClick={() => stop.mutate(run.uid)}>
                          <StopRoundedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    {run.status !== 'running' && run.status !== 'pending' && (
                      <Tooltip title="Delete this run">
                        <IconButton size="small" onClick={() => remove.mutate(run.uid)}>
                          <DeleteOutlineRoundedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>New AutoML run</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <TextField
              size="small"
              fullWidth
              label="Run name"
              placeholder="Optional"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
            <RunConfigForm
              value={config}
              onChange={setConfig}
              initialPipeline={useEditorPipeline ? editorGraph : null}
            />
            {editorGraph.nodes.length > 0 && (
              <Button
                size="small"
                variant={useEditorPipeline ? 'contained' : 'outlined'}
                onClick={() => setUseEditorPipeline((state) => !state)}
                sx={{ alignSelf: 'flex-start' }}
              >
                {useEditorPipeline ? 'Using the editor pipeline as the starting point' : 'Start from the pipeline in the editor'}
              </Button>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => start.mutate()}
            disabled={!config.dataset_uid || start.isPending}
            startIcon={<PlayArrowRoundedIcon />}
          >
            {start.isPending ? 'Starting…' : 'Start'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
