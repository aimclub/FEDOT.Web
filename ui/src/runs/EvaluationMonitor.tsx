import { useQuery } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'

import { api } from '../api/client'
import type { ActiveEvaluation, FinishedEvaluation } from '../api/types'

interface Props {
  runUid: string
  /** Total folds from the run config, to render "fold 2 of 3". */
  cvFolds?: number | null
}

const mono = '"JetBrains Mono", monospace'

const opsLabel = (ops: string[]): string => (ops.length > 0 ? ops.join(' → ') : 'pipeline')

const fmtSeconds = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '—'
  if (value < 60) return `${Math.round(value)}s`
  return `${Math.floor(value / 60)}m ${Math.round(value % 60)}s`
}

function ActiveRow({ item, cvFolds }: { item: ActiveEvaluation; cvFolds?: number | null }) {
  const theme = useTheme()
  return (
    <Stack direction="row" alignItems="center" spacing={1} sx={{ minWidth: 0 }}>
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          flexShrink: 0,
          bgcolor: theme.palette.success.main,
          animation: 'evalPulse 1.2s ease-in-out infinite',
          '@keyframes evalPulse': {
            '0%': { opacity: 1 },
            '50%': { opacity: 0.3 },
            '100%': { opacity: 1 },
          },
        }}
      />
      <Typography
        noWrap
        sx={{ fontFamily: mono, fontSize: '0.78rem', minWidth: 0, flexShrink: 1 }}
        title={opsLabel(item.ops)}
      >
        {opsLabel(item.ops)}
      </Typography>
      {item.fold !== null && (
        <Chip
          size="small"
          variant="outlined"
          label={cvFolds ? `fold ${item.fold + 1}/${cvFolds}` : `fold ${item.fold + 1}`}
          sx={{ height: 19, fontSize: '0.68rem', flexShrink: 0 }}
        />
      )}
      {item.node && (
        <Chip
          size="small"
          color="success"
          variant="outlined"
          label={`fitting ${item.node}`}
          sx={{ height: 19, fontSize: '0.68rem', flexShrink: 0 }}
        />
      )}
      <Box sx={{ flexGrow: 1 }} />
      <Typography sx={{ fontSize: '0.72rem', color: 'text.secondary', flexShrink: 0 }}>
        {fmtSeconds(item.seconds)}
      </Typography>
    </Stack>
  )
}

function RecentRow({ item }: { item: FinishedEvaluation }) {
  const theme = useTheme()
  return (
    <Stack direction="row" alignItems="center" spacing={1} sx={{ minWidth: 0 }}>
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          flexShrink: 0,
          bgcolor: item.failed ? theme.palette.error.main : alpha(theme.palette.text.disabled, 0.5),
        }}
      />
      <Typography
        noWrap
        sx={{
          fontFamily: mono,
          fontSize: '0.78rem',
          minWidth: 0,
          color: item.failed ? 'text.disabled' : 'text.primary',
        }}
        title={item.error ?? opsLabel(item.ops)}
      >
        {opsLabel(item.ops)}
      </Typography>
      {item.failed && (
        <Tooltip title={item.error ?? 'The evaluation failed'}>
          <Chip size="small" color="error" variant="outlined" label="failed" sx={{ height: 19, fontSize: '0.68rem' }} />
        </Tooltip>
      )}
      <Box sx={{ flexGrow: 1 }} />
      {item.fitness !== null && (
        <Typography sx={{ fontFamily: mono, fontSize: '0.72rem', flexShrink: 0 }}>
          {Number(item.fitness.toFixed(4))}
        </Typography>
      )}
      <Typography sx={{ fontSize: '0.72rem', color: 'text.secondary', flexShrink: 0, width: 52, textAlign: 'right' }}>
        {fmtSeconds(item.seconds)}
      </Typography>
    </Stack>
  )
}

/**
 * What the evaluator is doing right now.
 *
 * A generation is minutes of silence in which the actual work happens: each
 * candidate pipeline is fitted fold after fold, node after node. This panel
 * shows that work as it goes — which pipelines are being fitted at this
 * moment, how long each has been going, and what just finished with what
 * fitness — so a slow run reads as slow *at something*, not stuck.
 */
export default function EvaluationMonitor({ runUid, cvFolds }: Props) {
  const { data } = useQuery({
    queryKey: ['evaluations', runUid],
    queryFn: () => api.evaluations(runUid),
    refetchInterval: 2000,
  })

  // The panel stays visible from the first second of a run: knowing that
  // nothing has been reported yet is also status.
  const { active, preparing, recent, totals } = data ?? {
    active: [],
    preparing: null,
    recent: [],
    totals: { done: 0, failed: 0, active: 0, mean_seconds: null },
  }
  const empty = active.length === 0 && recent.length === 0 && !preparing

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" alignItems="baseline" spacing={1} sx={{ mb: 1 }}>
        <Typography variant="subtitle2">Evaluating now</Typography>
        <Typography variant="caption" color="text.secondary">
          {totals.done} evaluated
          {totals.failed > 0 && ` · ${totals.failed} failed`}
          {totals.mean_seconds !== null && ` · ~${fmtSeconds(totals.mean_seconds)} per pipeline`}
        </Typography>
      </Stack>

      <Stack spacing={0.75}>
        {preparing && (
          <Stack direction="row" alignItems="center" spacing={1}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: 'info.main',
                animation: 'evalPulse 1.2s ease-in-out infinite',
              }}
            />
            <Typography sx={{ fontSize: '0.78rem' }}>
              Fitting outside evolution (initial assumption or final model)
              {preparing.node && (
                <Box component="span" sx={{ fontFamily: mono }}>
                  {' '}
                  — {preparing.node}
                </Box>
              )}
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            <Typography sx={{ fontSize: '0.72rem', color: 'text.secondary' }}>
              {fmtSeconds(preparing.seconds)}
            </Typography>
          </Stack>
        )}

        {active.map((item, index) => (
          <ActiveRow key={index} item={item} cvFolds={cvFolds} />
        ))}

        {active.length === 0 && !preparing && (
          <Typography variant="caption" color="text.disabled">
            {empty
              ? 'Nothing reported yet — the run is starting up. Fits appear here the moment they begin.'
              : 'Nothing is being fitted right now — the optimiser is breeding the next population: selection, mutation, crossover and verification of the offspring.'}
          </Typography>
        )}
      </Stack>

      {recent.length > 0 && (
        <>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5, mb: 0.5 }}>
            Just finished
          </Typography>
          <Stack spacing={0.5}>
            {recent.slice(0, 6).map((item, index) => (
              <RecentRow key={index} item={item} />
            ))}
          </Stack>
        </>
      )}
    </Paper>
  )
}
