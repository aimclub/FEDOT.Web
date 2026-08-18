import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import Grid from '@mui/material/Grid'
import LinearProgress from '@mui/material/LinearProgress'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Tab from '@mui/material/Tab'
import Tabs from '@mui/material/Tabs'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import CalculateRoundedIcon from '@mui/icons-material/CalculateRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import FiberManualRecordRoundedIcon from '@mui/icons-material/FiberManualRecordRounded'
import ScienceRoundedIcon from '@mui/icons-material/ScienceRounded'
import StopRoundedIcon from '@mui/icons-material/StopRounded'

import { api } from '../api/client'
import type { GenerationPoint, PipelineGraph, RunStatus } from '../api/types'
import ObjectiveBreakdown from '../analysis/ObjectiveBreakdown'
import SensitivityPanel from '../analysis/SensitivityPanel'
import EvolutionHistory from '../history/EvolutionHistory'
import NodeInspector from '../pipeline/NodeInspector'
import PipelineCanvas from '../pipeline/PipelineCanvas'
import { useEditorStore } from '../pipeline/editorStore'
import EvolutionControlPanel from '../runs/EvolutionControlPanel'
import EvaluationMonitor from '../runs/EvaluationMonitor'
import FitnessChart from '../runs/FitnessChart'
import { useRunStream } from '../runs/useRunStream'

const LIVE: RunStatus[] = ['pending', 'running']

const STATUS_COLOR: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  running: 'info',
  finished: 'success',
  failed: 'error',
  cancelled: 'warning',
}

export default function RunDetailPage() {
  const { uid } = useParams<{ uid: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const setGraph = useEditorStore((state) => state.setGraph)
  const setTask = useEditorStore((state) => state.setTask)

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [tab, setTab] = useState<'pipeline' | 'history'>('pipeline')
  const [objectiveOpen, setObjectiveOpen] = useState(false)
  const [sensitivityOpen, setSensitivityOpen] = useState(false)

  const { data: progress, isLoading } = useQuery({
    queryKey: ['run-progress', uid],
    queryFn: () => api.runProgress(uid!),
    enabled: Boolean(uid),
    refetchInterval: (query) =>
      LIVE.includes(query.state.data?.run.status as RunStatus) ? 5000 : false,
  })

  const isLive = LIVE.includes(progress?.run.status as RunStatus)
  const stream = useRunStream(uid, isLive)

  const stop = useMutation({
    mutationFn: () => api.stopRun(uid!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['run-progress', uid] })
      queryClient.invalidateQueries({ queryKey: ['runs'] })
    },
  })

  // The socket is normally ahead of the 5-second snapshot, but after a dropped
  // connection the snapshot becomes the fresher source — without this the chart
  // would freeze at wherever the socket died while polling kept working.
  const generations: GenerationPoint[] = useMemo(() => {
    const snapshot = progress?.generations ?? []
    return stream.generations.length >= snapshot.length ? stream.generations : snapshot
  }, [stream.generations, progress?.generations])

  const bestPipeline: PipelineGraph | null =
    progress?.best_pipeline ?? stream.bestPipeline ?? null

  const selectedNode = useMemo(
    () => bestPipeline?.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [bestPipeline, selectedNodeId],
  )

  const latest = generations[generations.length - 1]
  const plannedGenerations = Number(progress?.run.config?.num_of_generations ?? 0)
  const percent =
    plannedGenerations > 0 && latest
      ? Math.min(100, (latest.generation / plannedGenerations) * 100)
      : null

  if (isLoading) {
    return (
      <Stack alignItems="center" sx={{ py: 6 }}>
        <CircularProgress size={26} />
      </Stack>
    )
  }

  if (!progress) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">This run could not be found.</Alert>
      </Box>
    )
  }

  const { run } = progress

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', p: 3 }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 2 }}>
        <Button size="small" startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/runs')}>
          Runs
        </Button>
        <Divider orientation="vertical" flexItem />
        <Typography variant="h1" sx={{ fontSize: '1.25rem' }}>
          {run.name}
        </Typography>
        <Chip size="small" color={STATUS_COLOR[run.status] ?? 'default'} label={run.status} />
        {isLive && (
          <Tooltip title={stream.connected ? 'Streaming live progress' : 'Reconnecting…'}>
            <Chip
              size="small"
              variant="outlined"
              color={stream.connected ? 'success' : 'warning'}
              label={stream.connected ? 'live' : 'offline'}
            />
          </Tooltip>
        )}
        <Box sx={{ flexGrow: 1 }} />
        {isLive && (
          <Button
            size="small"
            color="error"
            variant="outlined"
            startIcon={<StopRoundedIcon />}
            onClick={() => stop.mutate()}
            disabled={stop.isPending}
          >
            Stop
          </Button>
        )}
      </Stack>

      {run.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {run.error}
        </Alert>
      )}

      {isLive && (
        <Box sx={{ mb: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {stream.status ?? 'running'}
              {latest ? ` · generation ${latest.generation}` : ''}
              {plannedGenerations ? ` of ${plannedGenerations}` : ''}
            </Typography>
          </Stack>
          <LinearProgress variant={percent === null ? 'indeterminate' : 'determinate'} value={percent ?? 0} />
        </Box>
      )}

      <Grid container spacing={2}>
        {isLive && (
          <Grid size={12}>
            <EvolutionControlPanel runUid={run.uid} revision={generations.length} />
          </Grid>
        )}

        {isLive && (
          <Grid size={12}>
            <EvaluationMonitor
              runUid={run.uid}
              cvFolds={typeof run.config?.cv_folds === 'number' ? run.config.cv_folds : null}
            />
          </Grid>
        )}

        <Grid size={{ xs: 12, lg: 7 }}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h3" sx={{ mb: 0.5 }}>
              Evolution
            </Typography>
            <FitnessChart generations={generations} />
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
              <Typography variant="h3">Result</Typography>
              <Box sx={{ flexGrow: 1 }} />
              <Tooltip title="Per-fold metrics behind the objective value, and the holdout score">
                <span>
                  <Button
                    size="small"
                    startIcon={<CalculateRoundedIcon fontSize="small" />}
                    onClick={() => setObjectiveOpen(true)}
                    disabled={!run.best_pipeline}
                  >
                    Objective
                  </Button>
                </span>
              </Tooltip>
              <Tooltip title="How much the score depends on each node and edge">
                <span>
                  <Button
                    size="small"
                    startIcon={<ScienceRoundedIcon fontSize="small" />}
                    onClick={() => setSensitivityOpen(true)}
                    disabled={!run.best_pipeline}
                  >
                    Sensitivity
                  </Button>
                </span>
              </Tooltip>
            </Stack>

            {run.metrics ? (
              <Stack spacing={0.75}>
                {Object.entries(run.metrics).map(([metric, score]) => (
                  <Stack key={metric} direction="row" alignItems="baseline" spacing={1}>
                    <Typography variant="body2" sx={{ minWidth: 96, color: 'text.secondary' }}>
                      {metric}
                    </Typography>
                    <Typography variant="h3" sx={{ fontFamily: '"JetBrains Mono", monospace' }}>
                      {score}
                    </Typography>
                  </Stack>
                ))}
                <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5 }}>
                  Measured on a holdout split the composer never saw.
                </Typography>
              </Stack>
            ) : (
              <Typography variant="body2" color="text.disabled">
                {isLive ? 'Metrics appear once the run finishes.' : 'No metrics were recorded.'}
              </Typography>
            )}

            <Divider sx={{ my: 1.5 }} />

            <Stack spacing={0.4}>
              {[
                ['Task', String(run.config?.problem ?? '—')],
                ['Preset', String(run.config?.preset ?? '—')],
                ['Time budget', `${run.config?.timeout ?? '—'} min`],
                ['Population', String(run.config?.pop_size ?? '—')],
                ['Generations run', String(generations.length)],
              ].map(([label, text]) => (
                <Stack key={label} direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">
                    {label}
                  </Typography>
                  <Typography variant="caption">{text}</Typography>
                </Stack>
              ))}
            </Stack>
          </Paper>
        </Grid>

        <Grid size={12}>
          <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
            <Tabs
              value={tab}
              onChange={(_, value) => setTab(value)}
              sx={{ px: 1, borderBottom: '1px solid', borderColor: 'divider', minHeight: 42 }}
            >
              <Tab
                label={isLive ? 'Current best pipeline' : 'Best pipeline'}
                value="pipeline"
                sx={{ minHeight: 42 }}
              />
              <Tab
                label="Evolution history"
                value="history"
                sx={{ minHeight: 42 }}
                icon={
                  isLive ? (
                    <FiberManualRecordRoundedIcon sx={{ fontSize: 10, color: 'info.main' }} />
                  ) : undefined
                }
                iconPosition="end"
              />
            </Tabs>

            {tab === 'history' && (
              <Box sx={{ height: 620 }}>
                <EvolutionHistory
                  runUid={run.uid}
                  isLive={isLive}
                  liveRevision={generations.length}
                  onOpenInEditor={async (individualUid) => {
                    const chosen = await api.lineagePipeline(run.uid, individualUid)
                    setGraph(chosen, { name: `${run.name} — gen ${chosen.generation}`, uid: null })
                    if (run.config?.problem) setTask(String(run.config.problem))
                    navigate('/editor')
                  }}
                />
              </Box>
            )}

            {tab === 'pipeline' && (
            <>
            <Stack
              direction="row"
              alignItems="center"
              spacing={1}
              sx={{ px: 2, py: 1.25, borderBottom: '1px solid', borderColor: 'divider' }}
            >
              {bestPipeline && (
                <>
                  <Chip size="small" variant="outlined" label={`${bestPipeline.nodes.length} nodes`} />
                  <Chip size="small" variant="outlined" label={`depth ${bestPipeline.depth}`} />
                </>
              )}
              <Box sx={{ flexGrow: 1 }} />
              {bestPipeline && (
                <Button
                  size="small"
                  startIcon={<EditRoundedIcon />}
                  onClick={() => {
                    setGraph(bestPipeline, { name: `${run.name} — copy`, uid: null })
                    if (run.config?.problem) setTask(String(run.config.problem))
                    navigate('/editor')
                  }}
                >
                  Open in editor
                </Button>
              )}
            </Stack>

            <Box sx={{ display: 'flex', height: 460 }}>
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <PipelineCanvas
                  graph={bestPipeline ?? { uid: '', nodes: [], edges: [], depth: 0, length: 0 }}
                  readOnly
                  selectedNodeId={selectedNodeId}
                  onSelect={setSelectedNodeId}
                  emptyHint={
                    isLive
                      ? 'The best pipeline appears after the first generation is evaluated.'
                      : 'This run produced no pipeline.'
                  }
                />
              </Box>
              {selectedNode && (
                <Box
                  sx={{
                    width: 356,
                    flexShrink: 0,
                    borderLeft: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <NodeInspector
                    node={selectedNode}
                    onParamsChange={() => {}}
                    onDelete={() => {}}
                    readOnly
                  />
                </Box>
              )}
            </Box>
            </>
            )}
          </Paper>
        </Grid>

        {stream.logs.length > 0 && (
          <Grid size={12}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h3" sx={{ mb: 1 }}>
                Log
              </Typography>
              <Box
                sx={{
                  maxHeight: 200,
                  overflowY: 'auto',
                  fontFamily: '"JetBrains Mono", monospace',
                  fontSize: '0.74rem',
                }}
              >
                {stream.logs.map((entry, index) => (
                  <Box
                    key={index}
                    sx={{ color: entry.level === 'error' ? 'error.main' : 'text.secondary' }}
                  >
                    {entry.elapsed != null ? `[${entry.elapsed.toFixed(1)}s] ` : ''}
                    {entry.message}
                  </Box>
                ))}
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>

      <ObjectiveBreakdown
        runUid={run.uid}
        open={objectiveOpen}
        onClose={() => setObjectiveOpen(false)}
      />
      <SensitivityPanel
        runUid={run.uid}
        open={sensitivityOpen}
        onClose={() => setSensitivityOpen(false)}
      />
    </Box>
  )
}
