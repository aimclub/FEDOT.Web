import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Accordion from '@mui/material/Accordion'
import AccordionDetails from '@mui/material/AccordionDetails'
import AccordionSummary from '@mui/material/AccordionSummary'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import FormControlLabel from '@mui/material/FormControlLabel'
import Grid from '@mui/material/Grid'
import MenuItem from '@mui/material/MenuItem'
import Slider from '@mui/material/Slider'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import ExpandMoreRoundedIcon from '@mui/icons-material/ExpandMoreRounded'

import { api } from '../api/client'
import type { PipelineGraph, Problem, RunConfig } from '../api/types'

interface Props {
  value: RunConfig
  onChange: (config: RunConfig) => void
  initialPipeline?: PipelineGraph | null
}

export const defaultRunConfig = (datasetUid = ''): RunConfig => ({
  problem: 'classification',
  dataset_uid: datasetUid,
  target: null,
  timeout: 5,
  preset: 'auto',
  metric: null,
  seed: 42,
  n_jobs: 1,
  cv_folds: 5,
  pop_size: 20,
  num_of_generations: 20,
  max_depth: 6,
  max_arity: 4,
  with_tuning: true,
  early_stopping_iterations: null,
  available_operations: null,
  forecast_length: 30,
  initial_pipeline: null,
  logging_level: 20,
})

/**
 * The run-configuration form.
 *
 * Every field maps onto a parameter of `Fedot(...)`, which is what turns this
 * from a viewer into a control panel for the framework: the same knobs a script
 * would set are available here, with the choices FEDOT itself reports.
 */
export default function RunConfigForm({ value, onChange, initialPipeline }: Props) {
  const [expanded, setExpanded] = useState(false)

  const { data: capabilities } = useQuery({
    queryKey: ['capabilities'],
    queryFn: api.capabilities,
    staleTime: Infinity,
  })

  const { data: datasets = [] } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets })

  const dataset = datasets.find((item) => item.uid === value.dataset_uid) ?? null

  const metrics = useMemo(
    () =>
      (capabilities?.metrics ?? []).filter(
        (metric) => metric.tasks.length === 0 || metric.tasks.includes(value.problem),
      ),
    [capabilities, value.problem],
  )

  const set = <K extends keyof RunConfig>(key: K, next: RunConfig[K]) =>
    onChange({ ...value, [key]: next })

  // A metric chosen for one task rarely applies to another.
  useEffect(() => {
    if (value.metric && !metrics.some((metric) => metric.id === value.metric)) {
      onChange({ ...value, metric: null })
    }
  }, [metrics, value, onChange])

  // Adopt the dataset's own target and task when one is picked.
  useEffect(() => {
    if (!dataset) return
    const patch: Partial<RunConfig> = {}
    if (!value.target && dataset.target) patch.target = dataset.target
    if (dataset.task && dataset.task !== value.problem) patch.problem = dataset.task as Problem
    if (Object.keys(patch).length) onChange({ ...value, ...patch })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataset?.uid])

  return (
    <Stack spacing={2}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            select
            fullWidth
            size="small"
            label="Dataset"
            value={value.dataset_uid}
            onChange={(event) => set('dataset_uid', event.target.value)}
            helperText={dataset ? `${dataset.n_rows ?? '?'} rows` : 'Upload a dataset first'}
          >
            {datasets.map((item) => (
              <MenuItem key={item.uid} value={item.uid}>
                {item.name}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            select
            fullWidth
            size="small"
            label="Target column"
            value={value.target ?? ''}
            onChange={(event) => set('target', event.target.value)}
            disabled={!dataset}
          >
            {(dataset?.columns ?? []).map((column) => (
              <MenuItem key={column.name} value={column.name}>
                {column.name} · {column.type}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            select
            fullWidth
            size="small"
            label="Task"
            value={value.problem}
            onChange={(event) => set('problem', event.target.value as Problem)}
          >
            {(capabilities?.tasks ?? [])
              .filter((task) => task.id !== 'clustering')
              .map((task) => (
                <MenuItem key={task.id} value={task.id}>
                  {task.label}
                </MenuItem>
              ))}
          </TextField>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            select
            fullWidth
            size="small"
            label="Preset"
            value={value.preset}
            onChange={(event) => set('preset', event.target.value)}
            helperText={
              capabilities?.presets.find((preset) => preset.id === value.preset)?.description
            }
          >
            {(capabilities?.presets ?? []).map((preset) => (
              <MenuItem key={preset.id} value={preset.id}>
                {preset.label}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            select
            fullWidth
            size="small"
            label="Metric"
            value={value.metric ?? ''}
            onChange={(event) => set('metric', event.target.value || null)}
            helperText="Leave empty to use FEDOT's default for the task"
          >
            <MenuItem value="">Default</MenuItem>
            {metrics.map((metric) => (
              <MenuItem key={metric.id} value={metric.id}>
                {metric.label}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid size={12}>
          <Typography variant="caption" color="text.secondary">
            Time budget — {value.timeout} minute{value.timeout === 1 ? '' : 's'}
          </Typography>
          <Slider
            size="small"
            value={value.timeout}
            min={0.5}
            max={Math.min(120, capabilities?.max_run_timeout_minutes ?? 120)}
            step={0.5}
            marks={[
              { value: 1, label: '1m' },
              { value: 15, label: '15m' },
              { value: 60, label: '1h' },
            ]}
            onChange={(_, next) => set('timeout', next as number)}
            valueLabelDisplay="auto"
          />
        </Grid>

        {value.problem === 'ts_forecasting' && (
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Forecast horizon"
              value={value.forecast_length}
              onChange={(event) => set('forecast_length', Number(event.target.value))}
              helperText="Number of future steps to predict"
            />
          </Grid>
        )}
      </Grid>

      {initialPipeline && initialPipeline.nodes.length > 0 && (
        <Alert severity="info" variant="outlined">
          Evolution will start from your pipeline ({initialPipeline.nodes.length} nodes) instead of
          FEDOT's default assumption.
        </Alert>
      )}

      <Accordion
        expanded={expanded}
        onChange={(_, isExpanded) => setExpanded(isExpanded)}
        disableGutters
        variant="outlined"
      >
        <AccordionSummary expandIcon={<ExpandMoreRoundedIcon />}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="subtitle2">Evolution parameters</Typography>
            <Chip
              size="small"
              variant="outlined"
              label={`pop ${value.pop_size} · gen ${value.num_of_generations}`}
            />
          </Stack>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Tooltip title="Number of pipelines held in each generation">
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Population size"
                  value={value.pop_size}
                  onChange={(event) => set('pop_size', Number(event.target.value))}
                />
              </Tooltip>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Generations"
                value={value.num_of_generations}
                onChange={(event) => set('num_of_generations', Number(event.target.value))}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Tooltip title="Longest chain of operations a pipeline may have">
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Max depth"
                  value={value.max_depth}
                  onChange={(event) => set('max_depth', Number(event.target.value))}
                />
              </Tooltip>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Tooltip title="Most parents a single node may take">
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Max arity"
                  value={value.max_arity}
                  onChange={(event) => set('max_arity', Number(event.target.value))}
                />
              </Tooltip>
            </Grid>

            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="CV folds"
                value={value.cv_folds}
                onChange={(event) => set('cv_folds', Number(event.target.value))}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Tooltip title="Stop early after this many generations without improvement">
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Early stopping"
                  value={value.early_stopping_iterations ?? ''}
                  onChange={(event) =>
                    set(
                      'early_stopping_iterations',
                      event.target.value ? Number(event.target.value) : null,
                    )
                  }
                />
              </Tooltip>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Parallel jobs"
                value={value.n_jobs}
                onChange={(event) => set('n_jobs', Number(event.target.value))}
                helperText="-1 uses every core"
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Seed"
                value={value.seed ?? ''}
                onChange={(event) =>
                  set('seed', event.target.value ? Number(event.target.value) : null)
                }
                helperText="Fixes the run for reproducibility"
              />
            </Grid>

            <Grid size={12}>
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={value.with_tuning}
                    onChange={(event) => set('with_tuning', event.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Tune hyperparameters after composition</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Runs the FEDOT tuner over the best pipeline within the same time budget
                    </Typography>
                  </Box>
                }
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Stack>
  )
}
