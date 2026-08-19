import { useEffect, useMemo, useState } from 'react'
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
import ContentCopyRoundedIcon from '@mui/icons-material/ContentCopyRounded'
import FiberManualRecordRoundedIcon from '@mui/icons-material/FiberManualRecordRounded'
import StopRoundedIcon from '@mui/icons-material/StopRounded'

import { epdeApi } from '../api/client'
import EquationView from '../equations/EquationView'
import TermTable from '../equations/TermTable'
import EvolutionHistory from '../history/EvolutionHistory'
import EvolutionControlPanel from '../runs/EvolutionControlPanel'
import ObjectiveChart from '../runs/ObjectiveChart'
import ParetoChart from '../runs/ParetoChart'
import { useEpdeRunStream } from '../runs/useEpdeRunStream'
import type { AblationReport, FrontEntry, GenerationPoint, ParetoPoint, RunStatus } from '../api/types'

const LIVE: RunStatus[] = ['pending', 'running']

/** Only a finished run carries per-term ablation. */
const ablationOf = (entry: ParetoPoint | FrontEntry | null): AblationReport[] =>
  entry && 'ablation' in entry ? (entry.ablation ?? []) : []

const STATUS_COLOR: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  running: 'info',
  finished: 'success',
  failed: 'error',
  cancelled: 'warning',
}

export default function EpdeRunDetailPage() {
  const { uid } = useParams<{ uid: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<'result' | 'history'>('result')
  const [selectedUid, setSelectedUid] = useState<string | null>(null)
  const [highlightTerm, setHighlightTerm] = useState<string | null>(null)

  const { data: capabilities } = useQuery({
    queryKey: ['epde-capabilities'],
    queryFn: epdeApi.capabilities,
    staleTime: Infinity,
  })

  const { data: progress, isLoading } = useQuery({
    queryKey: ['epde-progress', uid],
    queryFn: () => epdeApi.progress(uid!),
    enabled: Boolean(uid),
    refetchInterval: (query) =>
      LIVE.includes(query.state.data?.run.status as RunStatus) ? 5000 : false,
  })

  // Two different questions. `isStreaming` decides whether to hold a socket
  // open, and must not depend on anything the socket reports or the two would
  // chase each other: tearing the socket down resets its state, which would
  // reopen it, which would report the end again.
  const isStreaming = LIVE.includes(progress?.run.status as RunStatus)
  const stream = useEpdeRunStream(uid, isStreaming)

  // `isLive` decides what the page shows. The socket learns the run ended
  // before the snapshot query does — and in a background tab the query's
  // interval is paused altogether, so the page would otherwise keep offering
  // Stop and a steering panel for a run that is already over.
  const isLive = isStreaming && !stream.terminal

  // The socket knows the run ended before the five-second poll does — and the
  // poll can be throttled altogether in a background tab. Refetching on the
  // socket's word is what switches the page from "running" to the result
  // without waiting for a tick that may not come.
  useEffect(() => {
    if (!stream.terminal) return
    queryClient.invalidateQueries({ queryKey: ['epde-progress', uid] })
    queryClient.invalidateQueries({ queryKey: ['epde-result', uid] })
    queryClient.invalidateQueries({ queryKey: ['epde-runs'] })
  }, [stream.terminal, uid, queryClient])

  const { data: result } = useQuery({
    queryKey: ['epde-result', uid],
    queryFn: () => epdeApi.result(uid!),
    enabled: Boolean(uid) && progress?.run.status === 'finished',
    retry: false,
  })

  const stop = useMutation({
    mutationFn: () => epdeApi.stopRun(uid!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epde-progress', uid] })
      queryClient.invalidateQueries({ queryKey: ['epde-runs'] })
    },
  })

  // The socket is normally ahead of the five-second snapshot, but after a
  // dropped connection the snapshot becomes the fresher source — without this
  // the chart would freeze wherever the socket died while polling kept working.
  const generations: GenerationPoint[] = useMemo(() => {
    const snapshot = progress?.generations ?? []
    return stream.generations.length >= snapshot.length ? stream.generations : snapshot
  }, [stream.generations, progress?.generations])

  const objectiveNames = progress?.objective_names?.length
    ? progress.objective_names
    : stream.objectiveNames

  // While the run is going the front comes from the progress snapshot, which
  // carries no ablation: that is computed once, at the end, where the token
  // cache is still alive.
  const front: (ParetoPoint | FrontEntry)[] = result?.front ?? progress?.front ?? []
  const selected = front.find((entry) => entry.uid === selectedUid) ?? front[0] ?? null

  const selectedSystem = useMemo(() => {
    if (selected && result?.best_system && selected.uid === result.best_system.uid) {
      return result.best_system
    }
    return null
  }, [selected, result])

  const displayed = selectedSystem ?? progress?.best_system ?? stream.best ?? null

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
  // Same reason as `isLive`: once the socket has reported the end, it is the
  // fresher source, and a background tab may never refetch the snapshot that
  // still calls the run running.
  const status = (stream.terminal && stream.status) || run.status
  const plannedGenerations = Number(run.config?.epochs ?? 0)
  const latest = generations[generations.length - 1]
  const percent =
    plannedGenerations > 0 && latest
      ? Math.min(100, (latest.generation / plannedGenerations) * 100)
      : null

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', p: 3 }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 2 }}>
        <Button size="small" startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/epde/runs')}>
          Searches
        </Button>
        <Divider orientation="vertical" flexItem />
        <Typography variant="h1" sx={{ fontSize: '1.25rem' }}>
          {run.name}
        </Typography>
        <Chip size="small" color={STATUS_COLOR[status] ?? 'default'} label={status} />
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
          <Tooltip title="Kill the run and throw away what it has. To keep the result, use Finish now in the steering panel.">
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
          </Tooltip>
        )}
      </Stack>

      {run.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {run.error}
        </Alert>
      )}

      {result?.finished_early && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {result.finished_early} — the population at that point is what is reported below.
        </Alert>
      )}

      {(result?.warnings ?? []).map((warning, index) => (
        <Alert key={index} severity="warning" variant="outlined" sx={{ mb: 1 }}>
          {warning}
        </Alert>
      ))}

      {isLive && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary">
            {stream.status ?? 'running'}
            {latest ? ` · generation ${latest.generation}` : ''}
            {plannedGenerations ? ` of ${plannedGenerations}` : ''}
            {stream.progress
              ? ` · sector ${stream.progress.sector}/${stream.progress.sectors}`
              : ''}
          </Typography>
          <LinearProgress
            variant={percent === null ? 'indeterminate' : 'determinate'}
            value={percent ?? 0}
          />
        </Box>
      )}

      <Grid container spacing={2}>
        {isLive && capabilities && (
          <Grid size={12}>
            <EvolutionControlPanel
              runUid={run.uid}
              controls={capabilities.controls}
              revision={stream.revision}
            />
          </Grid>
        )}

        <Grid size={{ xs: 12, lg: 6 }}>
          <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
            <Typography variant="h3" sx={{ mb: 0.5 }}>
              Objectives
            </Typography>
            <ObjectiveChart generations={generations} objectiveNames={objectiveNames} />
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, lg: 6 }}>
          <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
            <Stack direction="row" alignItems="baseline" spacing={1} sx={{ mb: 0.5 }}>
              <Typography variant="h3">Trade-off</Typography>
              <Typography variant="caption" color="text.disabled">
                both axes are minimised; the useful corner is the bottom left
              </Typography>
            </Stack>
            <ParetoChart
              front={front}
              objectiveNames={objectiveNames}
              selectedUid={selected?.uid ?? null}
              onSelect={setSelectedUid}
            />
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
                label={isLive ? 'Leading equation' : 'Discovered equations'}
                value="result"
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
              <Box sx={{ height: 640 }}>
                <EvolutionHistory runUid={run.uid} isLive={isLive} liveRevision={stream.revision} />
              </Box>
            )}

            {tab === 'result' && (
              <Box sx={{ p: 2 }}>
                {front.length > 1 && (
                  <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }} useFlexGap>
                    {front.map((entry) => (
                      <Chip
                        key={entry.uid}
                        size="small"
                        variant={entry.uid === selected?.uid ? 'filled' : 'outlined'}
                        color={entry.uid === selected?.uid ? 'primary' : 'default'}
                        label={`${entry.active_terms} terms · ${Number(
                          (entry.objectives[0] ?? 0).toPrecision(3),
                        )}`}
                        onClick={() => setSelectedUid(entry.uid)}
                      />
                    ))}
                  </Stack>
                )}

                {selected ? (
                  <Stack spacing={2}>
                    <Box>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Typography variant="caption" color="text.secondary">
                          candidate {selected.uid}
                        </Typography>
                        <Box sx={{ flexGrow: 1 }} />
                        <Tooltip title="Copy the LaTeX form, for pasting into a paper">
                          <Button
                            size="small"
                            startIcon={<ContentCopyRoundedIcon fontSize="small" />}
                            onClick={() => void navigator.clipboard?.writeText(selected.latex)}
                          >
                            LaTeX
                          </Button>
                        </Tooltip>
                      </Stack>
                      {displayed && displayed.uid === selected.uid ? (
                        <EquationView system={displayed} highlightTermId={highlightTerm} />
                      ) : (
                        <Typography
                          sx={{
                            fontFamily: '"JetBrains Mono", monospace',
                            fontSize: '0.86rem',
                            whiteSpace: 'pre-wrap',
                          }}
                        >
                          {selected.text}
                        </Typography>
                      )}
                    </Box>

                    {ablationOf(selected).map((report) => {
                      const equation = displayed?.equations.find(
                        (entry) => entry.variable === report.variable,
                      )
                      if (!equation) return null
                      return (
                        <Box key={report.variable}>
                          <Typography variant="h3" sx={{ mb: 0.5 }}>
                            What it rests on{' '}
                            {ablationOf(selected).length > 1 && `· ${report.variable}`}
                          </Typography>
                          <TermTable
                            equation={equation}
                            ablation={report}
                            onHighlight={setHighlightTerm}
                          />
                        </Box>
                      )
                    })}
                  </Stack>
                ) : (
                  <EquationView
                    system={displayed}
                    emptyHint={
                      isLive
                        ? 'The leading equation appears once the first population is evaluated.'
                        : 'This run produced no equation.'
                    }
                  />
                )}
              </Box>
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
                  maxHeight: 220,
                  overflowY: 'auto',
                  fontFamily: '"JetBrains Mono", monospace',
                  fontSize: '0.74rem',
                }}
              >
                {stream.logs.map((entry, index) => (
                  <Box
                    key={index}
                    sx={{
                      color:
                        entry.level === 'error'
                          ? 'error.main'
                          : entry.level === 'warning'
                            ? 'warning.main'
                            : 'text.secondary',
                    }}
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
    </Box>
  )
}
