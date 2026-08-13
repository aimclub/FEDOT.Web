import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import Grid from '@mui/material/Grid'
import Paper from '@mui/material/Paper'
import Slider from '@mui/material/Slider'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import FlagRoundedIcon from '@mui/icons-material/FlagRounded'
import RestartAltRoundedIcon from '@mui/icons-material/RestartAltRounded'

import { api } from '../api/client'
import type { EvolutionControls } from '../api/types'

interface Props {
  runUid: string
  /** Bumped by the caller on each new generation, to refresh what is in force. */
  revision?: number
}

const number = (value: string): number | null => {
  if (value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const show = (value: number | null | undefined, digits = 2): string =>
  value === null || value === undefined ? '—' : String(Number(value.toFixed(digits)))

/**
 * Change how the evolution behaves, without restarting it.
 *
 * Requests are picked up by the optimiser between generations, so a generation in
 * flight is never disturbed — which is why a change shows up in "in force" one
 * generation after it is sent. Leaving a field empty hands that parameter back to
 * GOLEM's own adaptive policy.
 */
/** Numeric fields, and how long to wait after typing before sending. */
const NUMERIC_FIELDS = ['pop_size', 'num_of_generations', 'timeout_minutes'] as const
const COMMIT_DELAY_MS = 700

export default function EvolutionControlPanel({ runUid, revision = 0 }: Props) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)

  const { data: state } = useQuery({
    queryKey: ['controls', runUid],
    queryFn: () => api.controls(runUid),
    staleTime: 0,
  })

  useEffect(() => {
    void queryClient.invalidateQueries({ queryKey: ['controls', runUid] })
  }, [revision, runUid, queryClient])

  const send = useMutation({
    mutationFn: (patch: Partial<EvolutionControls>) => api.setControls(runUid, patch),
    onSuccess: (next) => {
      queryClient.setQueryData(['controls', runUid], next)
      setError(null)
    },
    onError: (sendError: Error) => setError(sendError.message),
  })

  const requested = state?.requested

  // Committing on a timer rather than on blur: a control panel should act on
  // what was typed without needing the field to lose focus first, and it makes
  // the behaviour independent of the render cycle.
  useEffect(() => {
    if (!requested || Object.keys(draft).length === 0) return
    const timer = window.setTimeout(() => {
      const patch: Partial<EvolutionControls> = {}
      for (const key of NUMERIC_FIELDS) {
        const pending = draft[key]
        if (pending === undefined) continue
        const parsed = number(pending)
        if (parsed !== (requested[key] ?? null)) {
          patch[key] = parsed
        }
      }
      setDraft({})
      if (Object.keys(patch).length > 0) send.mutate(patch)
    }, COMMIT_DELAY_MS)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft, requested])

  if (!state || !requested) return null

  const effective = state.effective

  const apply = (patch: Partial<EvolutionControls>) => {
    setDraft({})
    send.mutate(patch)
  }

  const field = (
    key: keyof EvolutionControls,
    label: string,
    hint: string,
    inForce: number | null | undefined,
  ) => {
    const pending = draft[key]
    const current = requested[key] as number | null
    const value = pending !== undefined ? pending : current === null ? '' : String(current)
    return (
      <Grid size={{ xs: 6, sm: 4 }}>
        <Tooltip title={hint}>
          <TextField
            size="small"
            fullWidth
            type="number"
            label={label}
            value={value}
            placeholder="adaptive"
            onChange={(event) => setDraft((state) => ({ ...state, [key]: event.target.value }))}
            helperText={
              pending !== undefined && number(pending) !== (current ?? null)
                ? 'sending…'
                : `in force: ${show(inForce)}`
            }
          />
        </Tooltip>
      </Grid>
    )
  }

  const probability = (
    key: 'mutation_prob' | 'crossover_prob',
    label: string,
    inForce: number | null | undefined,
  ) => {
    const current = requested[key]
    return (
      <Grid size={{ xs: 12, sm: 6 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Typography variant="caption" sx={{ minWidth: 96, color: 'text.secondary' }}>
            {label}
          </Typography>
          <Slider
            size="small"
            value={current ?? inForce ?? 0}
            min={0}
            max={1}
            step={0.05}
            valueLabelDisplay="auto"
            onChangeCommitted={(_, value) =>
              apply({ [key]: value as number } as Partial<EvolutionControls>)
            }
            sx={{ flexGrow: 1 }}
          />
          <Typography
            variant="caption"
            sx={{ width: 74, textAlign: 'right', fontFamily: '"JetBrains Mono", monospace' }}
          >
            {show(inForce)}
            {current === null && (
              <Typography component="span" variant="caption" color="text.disabled">
                {' '}
                auto
              </Typography>
            )}
          </Typography>
        </Stack>
      </Grid>
    )
  }

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <Typography variant="h3">Evolution controls</Typography>
        {effective && (
          <Chip size="small" variant="outlined" label={`generation ${effective.generation}`} />
        )}
        <Box sx={{ flexGrow: 1 }} />
        <Tooltip title="Hand every parameter back to GOLEM's adaptive policy">
          <Button
            size="small"
            startIcon={<RestartAltRoundedIcon />}
            onClick={() =>
              apply({
                pop_size: null,
                num_of_generations: null,
                timeout_minutes: null,
                mutation_prob: null,
                crossover_prob: null,
              })
            }
          >
            Reset
          </Button>
        </Tooltip>
        <Tooltip title="Stop after the current generation and keep the best pipeline found so far. Unlike Stop, the result is fitted and saved.">
          <Button
            size="small"
            color="warning"
            variant="outlined"
            startIcon={<FlagRoundedIcon />}
            onClick={() => apply({ finish_now: true })}
          >
            Finish now
          </Button>
        </Tooltip>
      </Stack>

      <Typography variant="caption" color="text.secondary">
        Changes are picked up between generations — a generation already running is never
        disturbed. An empty field means GOLEM decides.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mt: 1 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        {field(
          'pop_size',
          'Population size',
          'How many pipelines each generation holds. GOLEM grows this on its own unless pinned.',
          effective?.pop_size,
        )}
        {field(
          'num_of_generations',
          'Generation limit',
          'The run stops once this many generations have been evaluated.',
          effective?.num_of_generations,
        )}
        {field(
          'timeout_minutes',
          'Time budget, min',
          'Total composition budget. Raising it mid-run buys more generations.',
          effective?.timeout_minutes,
        )}
      </Grid>

      <Divider sx={{ my: 1.5 }} />

      <Grid container spacing={2}>
        {probability('mutation_prob', 'Mutation', effective?.mutation_prob)}
        {probability('crossover_prob', 'Crossover', effective?.crossover_prob)}
      </Grid>

      {state.applied.length > 0 && (
        <Alert severity="success" variant="outlined" sx={{ mt: 1.5, py: 0.2 }}>
          {state.applied.join(' · ')}
        </Alert>
      )}
    </Paper>
  )
}
