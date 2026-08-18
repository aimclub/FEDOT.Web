import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import LinearProgress from '@mui/material/LinearProgress'
import MenuItem from '@mui/material/MenuItem'
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
import { alpha, useTheme } from '@mui/material/styles'

import { api } from '../api/client'
import type { PipelineGraph, SensitivityEntity, SensitivityResult } from '../api/types'
import { useAnalysis, useStandaloneAnalysis } from './useAnalysis'

interface Props {
  /** Analyse a pipeline of this run (the run supplies the dataset). */
  runUid?: string
  /** Or analyse a free-standing pipeline; the user then picks the dataset. */
  standalone?: { graph: PipelineGraph; task: string | null }
  open: boolean
  onClose: () => void
}

/**
 * GOLEM reports each change as a sign-normalised score ratio, and its own
 * optimiser applies changes at ratio > 1: above 1 means the change *improved*
 * the objective — that part is dead weight or replaceable — and below 1 means
 * the pipeline relies on it. Exactly -1 is GOLEM's could-not-evaluate sentinel.
 *
 * The backend ships the verdict as `improves`; the fallback below re-derives it
 * for results computed before that field existed.
 */
const verdictOf = (entity: SensitivityEntity): boolean | null => {
  if (typeof entity.improves === 'boolean') return entity.improves
  if (entity.improves === null) return null
  const value = entity.worst?.value
  if (typeof value !== 'number' || !Number.isFinite(value) || value === -1) return null
  return value > 1
}

const severityOf = (entity: SensitivityEntity): number => {
  if (typeof entity.severity === 'number') return entity.severity
  const value = entity.worst?.value
  if (typeof value !== 'number' || !Number.isFinite(value) || value === -1) return 0
  return Math.abs(value - 1)
}

const ratioOf = (entity: SensitivityEntity): number | null => {
  const value = entity.worst?.value
  return typeof value === 'number' && Number.isFinite(value) && value !== -1 ? value : null
}

export default function SensitivityPanel({ runUid, standalone, open, onClose }: Props) {
  const theme = useTheme()
  // Both hooks are called to keep the hook order stable; only one is live.
  const runAnalysis = useAnalysis(runUid ?? '', 'sensitivity')
  const standaloneAnalysis = useStandaloneAnalysis('sensitivity')
  const { startError, record, isRunning, isCached } = standalone ? standaloneAnalysis : runAnalysis

  const [datasetUid, setDatasetUid] = useState('')
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: api.datasets,
    enabled: Boolean(standalone) && open,
  })
  const matchingDatasets = useMemo(
    () =>
      (datasets ?? []).filter(
        (dataset) => !standalone?.task || !dataset.task || dataset.task === standalone.task,
      ),
    [datasets, standalone?.task],
  )

  const start = (options: { replacements: number }) => {
    if (standalone) {
      void standaloneAnalysis.start({
        graph: standalone.graph,
        dataset_uid: datasetUid,
        problem: standalone.task ?? undefined,
        replacements: options.replacements,
      })
    } else {
      void runAnalysis.start(options)
    }
  }

  const result = record?.status === 'finished' ? (record.result as SensitivityResult) : null

  const rows = useMemo(() => {
    if (!result) return []
    // Biggest effect first, whichever direction it points.
    return [...result.entities].sort((a, b) => severityOf(b) - severityOf(a))
  }, [result])

  const scale = useMemo(() => Math.max(...rows.map(severityOf), 0.01), [rows])

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ pb: 1 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Box>
            <Typography variant="h2" component="span">
              Sensitivity
            </Typography>
            <Typography variant="body2" color="text.secondary">
              What the pipeline's score actually rests on.
            </Typography>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          {result && isCached && (
            <Tooltip title="Shown from an earlier run of this analysis">
              <Chip size="small" variant="outlined" label="cached" />
            </Tooltip>
          )}
          {result && <Chip size="small" variant="outlined" label={result.metric} />}
        </Stack>
      </DialogTitle>

      <DialogContent dividers>
        {!record && !isRunning && (
          <Stack spacing={2} alignItems="flex-start">
            <Typography variant="body2" color="text.secondary">
              Runs GOLEM's structural analysis: each node is deleted, replaced and has its subtree
              removed, and each edge deleted and replaced — refitting the pipeline every time. This
              is the slowest thing here; expect it to take several times a single fit.
            </Typography>
            {standalone && (
              <TextField
                select
                size="small"
                label="Dataset to fit on"
                value={datasetUid}
                onChange={(event) => setDatasetUid(event.target.value)}
                helperText="The pipeline is fitted on this dataset before the analysis varies it."
                sx={{ minWidth: 320 }}
              >
                {matchingDatasets.length === 0 && (
                  <MenuItem value="" disabled>
                    No uploaded dataset fits this task
                  </MenuItem>
                )}
                {matchingDatasets.map((dataset) => (
                  <MenuItem key={dataset.uid} value={dataset.uid}>
                    {dataset.name} ({dataset.n_rows} rows)
                  </MenuItem>
                ))}
              </TextField>
            )}
            <Stack direction="row" spacing={1}>
              <Button
                variant="contained"
                onClick={() => start({ replacements: 2 })}
                disabled={Boolean(standalone) && !datasetUid}
              >
                Analyse
              </Button>
              <Button
                onClick={() => start({ replacements: 1 })}
                disabled={Boolean(standalone) && !datasetUid}
              >
                Quick pass
              </Button>
            </Stack>
          </Stack>
        )}

        {isRunning && (
          <Box sx={{ py: 3 }}>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
              Refitting the pipeline for each variant…
            </Typography>
          </Box>
        )}

        {startError && <Alert severity="error">{startError}</Alert>}
        {record?.status === 'failed' && <Alert severity="error">{record.error}</Alert>}

        {result && rows.length === 0 && (
          <Alert severity="info">
            The analysis returned nothing to show — a single-node pipeline has no structure to vary.
          </Alert>
        )}

        {result && rows.length > 0 && (
          <Stack spacing={2}>
            <Paper variant="outlined" sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Part</TableCell>
                    <TableCell>What it is</TableCell>
                    <TableCell>Worst change</TableCell>
                    <TableCell align="right">Score ratio</TableCell>
                    <TableCell sx={{ width: '32%' }}>Impact</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((entity) => {
                    const ratio = ratioOf(entity)
                    const improves = verdictOf(entity)
                    const severity = severityOf(entity)
                    const colour =
                      improves === null
                        ? theme.palette.text.disabled
                        : improves
                          ? theme.palette.warning.main
                          : theme.palette.info.main
                    const width = Math.min(100, (severity / scale) * 100)
                    return (
                      <TableRow key={`${entity.entity_type}:${entity.entity}`}>
                        <TableCell>
                          <Chip
                            size="small"
                            variant="outlined"
                            label={entity.entity_type}
                            sx={{ height: 19, fontSize: '0.68rem' }}
                          />
                        </TableCell>
                        <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.78rem' }}>
                          {entity.operation ?? entity.entity}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {entity.worst?.approach_name?.replace('Analyze', '') ?? '—'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right" sx={{ fontFamily: '"JetBrains Mono", monospace' }}>
                          {ratio === null ? '—' : ratio.toFixed(4)}
                        </TableCell>
                        <TableCell>
                          <Tooltip
                            title={
                              improves === null
                                ? 'This change could not be evaluated'
                                : improves
                                  ? 'Changing this part improved the score — it is dead weight or replaceable'
                                  : 'Changing this part hurt the score — the pipeline relies on it'
                            }
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box
                                sx={{
                                  height: 8,
                                  width: `${width}%`,
                                  minWidth: improves === null ? 0 : 3,
                                  borderRadius: 4,
                                  bgcolor: alpha(colour, 0.75),
                                }}
                              />
                              <Typography sx={{ fontSize: '0.68rem', color: 'text.disabled' }}>
                                {improves === null ? 'n/a' : improves ? 'change helps' : 'load-bearing'}
                              </Typography>
                            </Box>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </Paper>

            <Typography variant="caption" color="text.disabled">
              {/* Rendered locally rather than from the payload, so results cached
                  before the wording was corrected still read right. */}
              Each ratio compares the changed pipeline's score to the original's, sign-normalised
              by GOLEM: above 1 the change improved the objective, below 1 the pipeline relies on
              that part. "Worst change" names the modification with the largest effect.
            </Typography>
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        {result && (
          <Button
            onClick={() => start({ replacements: 2 })}
            disabled={isRunning || (Boolean(standalone) && !datasetUid)}
          >
            Recompute
          </Button>
        )}
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
