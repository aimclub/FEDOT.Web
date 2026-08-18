import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Grid from '@mui/material/Grid'
import Paper from '@mui/material/Paper'
import Slider from '@mui/material/Slider'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import FlagRoundedIcon from '@mui/icons-material/FlagRounded'

import { epdeApi } from '../api/client'
import type { ControlInfo, EvolutionControls } from '../api/types'

/**
 * Steering the search without restarting it.
 *
 * EPDE has no requirements object to write to: each evolutionary operator owns
 * a `params` dict that it reads on every application, and the backend writes
 * into the live instances between generations. So a change here takes effect on
 * the next generation and never disturbs one in flight — which is also why a
 * change shows up in "in force" one generation after it is made.
 *
 * Two limits are structural rather than missing features, and are stated
 * instead of being offered and quietly ignored: the population size is fixed
 * (MOEA/D pairs every individual with a weight vector made at construction),
 * and the generation limit can only be lowered.
 */

interface Props {
  runUid: string
  controls: ControlInfo[]
  /** Bumped by the caller on every generation, so "in force" stays current. */
  revision: number
}

export default function EvolutionControlPanel({ runUid, controls, revision }: Props) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<Record<string, number | null>>({})

  const { data: state, refetch } = useQuery({
    queryKey: ['epde-controls', runUid],
    queryFn: () => epdeApi.controls(runUid),
  })

  useEffect(() => {
    void refetch()
  }, [revision, refetch])

  const patch = useMutation({
    mutationFn: (body: Partial<EvolutionControls>) => epdeApi.setControls(runUid, body),
    onSuccess: () => {
      setDraft({})
      queryClient.invalidateQueries({ queryKey: ['epde-controls', runUid] })
    },
  })

  if (!state) return null

  const available = new Set(state.available_operators)
  const supported = (control: ControlInfo) =>
    available.size === 0 || control.operators.some((key) => available.has(key))

  const valueOf = (control: ControlInfo) =>
    draft[control.name] ??
    state.requested[control.name as keyof EvolutionControls] ??
    state.effective[control.name] ??
    control.minimum

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <Typography variant="h3">Steering</Typography>
        <Tooltip title="Changes are picked up between generations, so a generation already in flight is never disturbed.">
          <Chip size="small" variant="outlined" label="applies next generation" />
        </Tooltip>
        <Box sx={{ flexGrow: 1 }} />
        <Tooltip title="Stop after the current generation and keep everything found so far. Unlike Stop, the run finishes through its normal path and still reports a result.">
          <span>
            <Button
              size="small"
              color="warning"
              variant="outlined"
              startIcon={<FlagRoundedIcon />}
              disabled={!state.can_control || patch.isPending}
              onClick={() => patch.mutate({ finish_now: true })}
            >
              Finish now
            </Button>
          </span>
        </Tooltip>
      </Stack>

      {state.applied.length > 0 && (
        <Alert severity="success" variant="outlined" sx={{ mb: 1.5, py: 0.25 }}>
          In force: {state.applied.join(', ')}
        </Alert>
      )}

      <Grid container spacing={2}>
        {controls.map((control) => {
          const enabled = state.can_control && supported(control)
          return (
            <Grid key={control.name} size={{ xs: 12, sm: 6, md: 4 }}>
              <Tooltip
                title={
                  supported(control)
                    ? control.description
                    : `This EPDE build has no ${control.operators.join(' or ')} operator, so the setting would land nowhere.`
                }
              >
                <Box>
                  <Stack direction="row" alignItems="baseline" spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      {control.label}
                    </Typography>
                    <Box sx={{ flexGrow: 1 }} />
                    <Typography
                      variant="caption"
                      sx={{ fontFamily: '"JetBrains Mono", monospace' }}
                      color={draft[control.name] !== undefined ? 'warning.main' : 'text.primary'}
                    >
                      {Number(valueOf(control)).toFixed(2)}
                    </Typography>
                  </Stack>
                  <Slider
                    size="small"
                    disabled={!enabled}
                    min={control.minimum}
                    max={control.maximum}
                    step={0.01}
                    value={Number(valueOf(control))}
                    onChange={(_, value) =>
                      setDraft((current) => ({ ...current, [control.name]: value as number }))
                    }
                    onChangeCommitted={(_, value) =>
                      patch.mutate({ [control.name]: value as number } as Partial<EvolutionControls>)
                    }
                  />
                  {state.effective[control.name] != null && (
                    <Typography variant="caption" color="text.disabled">
                      the search is using {Number(state.effective[control.name]).toFixed(2)}
                    </Typography>
                  )}
                </Box>
              </Tooltip>
            </Grid>
          )
        })}

        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Tooltip title="Lower the generation limit. EPDE captures the count when it starts, so this is enforced from outside: the run ends after the generation that reaches it, with its population intact.">
            <TextField
              size="small"
              fullWidth
              type="number"
              label="Stop after generation"
              disabled={!state.can_control}
              defaultValue={state.requested.epochs ?? ''}
              onBlur={(event) =>
                patch.mutate({ epochs: event.target.value ? Number(event.target.value) : null })
              }
            />
          </Tooltip>
        </Grid>
      </Grid>

      <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 1.5 }}>
        The population size cannot change mid-run: MOEA/D pairs every individual with a weight
        vector generated when the optimiser was built, and a new individual would have no sector to
        belong to.
      </Typography>
    </Paper>
  )
}
