import { useEffect, useMemo, useState } from 'react'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import FormControlLabel from '@mui/material/FormControlLabel'
import Grid from '@mui/material/Grid'
import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'

import type { DatasetRecord, EpdeCapabilities, EpdeRunConfig, SampleInfo } from '../api/types'

/**
 * Everything a search needs, with the couple of settings that actually decide
 * whether it finds anything given their own explanation.
 *
 * The derivative order is the one to get right: EPDE can only build terms out
 * of derivatives it computed, so looking for a wave equation with first-order
 * derivatives is looking for something that is not in the pool.
 */

interface Props {
  dataset: DatasetRecord
  capabilities: EpdeCapabilities
  sample?: SampleInfo | null
  busy?: boolean
  onStart: (config: EpdeRunConfig, name?: string) => void
}

const DEFAULTS: Omit<EpdeRunConfig, 'dataset_uid'> = {
  variables: null,
  multiobjective: true,
  population_size: 8,
  epochs: 15,
  timeout: 20,
  max_deriv_order: 2,
  equation_terms_max_number: 5,
  equation_factors_max_number: 1,
  sparsity_min: 1e-8,
  sparsity_max: 1.0,
  data_fun_pow: 1,
  boundary: 0,
  time_axis: 0,
  preprocessor: 'poly',
  preprocessor_kwargs: {},
  token_families: [],
  device: 'cpu',
  memory_for_cache: 15,
  seed: null,
}

export default function RunConfigForm({ dataset, capabilities, sample, busy, onStart }: Props) {
  const dimensions = dataset.shape.length
  const [config, setConfig] = useState<EpdeRunConfig>(() => ({
    ...DEFAULTS,
    dataset_uid: dataset.uid,
    variables: dataset.variables.map((variable) => variable.name),
    // One order per axis, so a field can be second order in space and first in
    // time without asking for derivatives nobody wants computed.
    max_deriv_order: Array(dimensions).fill(2),
    ...(sample?.suggestion as Partial<EpdeRunConfig> | undefined),
  }))
  const [name, setName] = useState('')

  useEffect(() => {
    setConfig((current) => ({
      ...current,
      dataset_uid: dataset.uid,
      variables: dataset.variables.map((variable) => variable.name),
      max_deriv_order: Array(dataset.shape.length).fill(
        Array.isArray(current.max_deriv_order) ? current.max_deriv_order[0] ?? 2 : current.max_deriv_order,
      ),
    }))
  }, [dataset.uid])

  const orders = useMemo(
    () =>
      Array.isArray(config.max_deriv_order)
        ? config.max_deriv_order
        : Array(dimensions).fill(config.max_deriv_order),
    [config.max_deriv_order, dimensions],
  )

  const set = <K extends keyof EpdeRunConfig>(key: K, value: EpdeRunConfig[K]) =>
    setConfig((current) => ({ ...current, [key]: value }))

  const toggleFamily = (id: string, on: boolean) =>
    setConfig((current) => ({
      ...current,
      token_families: on
        ? [...current.token_families, { id, params: {} }]
        : current.token_families.filter((family) => family.id !== id),
    }))

  const nodes = dataset.shape.reduce((total, size) => total * size, 1)
  const boundary = Array.isArray(config.boundary) ? config.boundary[0] : config.boundary
  const secondAxis = capabilities.features.physics_informed_criterion && config.use_pic !== false
    ? 'coefficient stability'
    : 'structural complexity'

  return (
    <Stack spacing={2}>
      <TextField
        size="small"
        label="Run name"
        placeholder={`${(config.variables ?? []).join('+')} on ${dataset.name}`}
        value={name}
        onChange={(event) => setName(event.target.value)}
      />

      {sample && (
        <Alert severity="info" variant="outlined">
          The settings below are the ones suggested for this example. It satisfies{' '}
          <Box component="code" sx={{ fontFamily: '"JetBrains Mono", monospace' }}>
            {sample.expected}
          </Box>
          .
        </Alert>
      )}

      <Box>
        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
          Variables to describe
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {dataset.variables.map((variable) => {
            const chosen = (config.variables ?? []).includes(variable.name)
            return (
              <Chip
                key={variable.name}
                label={variable.name}
                size="small"
                color={chosen ? 'primary' : 'default'}
                variant={chosen ? 'filled' : 'outlined'}
                onClick={() =>
                  set(
                    'variables',
                    chosen
                      ? (config.variables ?? []).filter((item) => item !== variable.name)
                      : [...(config.variables ?? []), variable.name],
                  )
                }
              />
            )
          })}
        </Stack>
        <Typography variant="caption" color="text.disabled">
          More than one means a system: EPDE discovers an equation for each, together.
        </Typography>
      </Box>

      <Divider />

      <Box>
        <Typography variant="subtitle2" sx={{ mb: 0.75 }}>
          Highest derivative per axis
        </Typography>
        <Stack direction="row" spacing={1.5}>
          {dataset.axes.map((axis, index) => (
            <TextField
              key={axis.name}
              size="small"
              type="number"
              label={axis.name}
              value={orders[index] ?? 2}
              inputProps={{ min: 1, max: 4 }}
              onChange={(event) => {
                const next = [...orders]
                next[index] = Math.max(1, Math.min(4, Number(event.target.value) || 1))
                set('max_deriv_order', next)
              }}
              sx={{ width: 100 }}
            />
          ))}
        </Stack>
        <Typography variant="caption" color="text.disabled">
          The search can only build terms from derivatives it computed. A wave equation needs 2 on
          both axes; every extra order costs preprocessing time and enlarges the pool.
        </Typography>
      </Box>

      <Grid container spacing={1.5}>
        <Grid size={6}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Terms per equation"
            value={config.equation_terms_max_number}
            inputProps={{ min: 2, max: 30 }}
            onChange={(event) =>
              set('equation_terms_max_number', Number(event.target.value) || 5)
            }
            helperText="Upper bound; sparse regression zeroes what it does not need"
          />
        </Grid>
        <Grid size={6}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Factors per term"
            value={
              typeof config.equation_factors_max_number === 'number'
                ? config.equation_factors_max_number
                : 2
            }
            inputProps={{ min: 1, max: 4 }}
            onChange={(event) =>
              set('equation_factors_max_number', Number(event.target.value) || 1)
            }
            helperText="2 or more allows products such as u·∂u/∂x"
          />
        </Grid>
        <Grid size={6}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Population"
            value={config.population_size}
            inputProps={{ min: 2, max: 200 }}
            onChange={(event) => set('population_size', Number(event.target.value) || 8)}
          />
        </Grid>
        <Grid size={6}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Generations"
            value={config.epochs}
            inputProps={{ min: 1, max: 1000 }}
            onChange={(event) => set('epochs', Number(event.target.value) || 10)}
          />
        </Grid>
        <Grid size={6}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Time budget (minutes)"
            value={config.timeout ?? ''}
            inputProps={{ min: 1, max: capabilities.max_run_timeout_minutes }}
            onChange={(event) =>
              set('timeout', event.target.value ? Number(event.target.value) : null)
            }
            helperText="EPDE has none of its own; enforced between generations"
          />
        </Grid>
        <Grid size={6}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Boundary width"
            value={boundary}
            inputProps={{ min: 0 }}
            onChange={(event) => set('boundary', Number(event.target.value) || 0)}
            helperText="Nodes ignored at each edge, where derivatives are worst"
          />
        </Grid>
      </Grid>

      <Divider />

      <Box>
        <Typography variant="subtitle2" sx={{ mb: 0.75 }}>
          Extra tokens
        </Typography>
        <Stack>
          {capabilities.token_families.map((family) => (
            <Tooltip
              key={family.id}
              title={
                family.available
                  ? family.description
                  : 'This EPDE build does not ship this token family.'
              }
            >
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    disabled={!family.available}
                    checked={config.token_families.some((entry) => entry.id === family.id)}
                    onChange={(event) => toggleFamily(family.id, event.target.checked)}
                  />
                }
                label={<Typography variant="body2">{family.label}</Typography>}
              />
            </Tooltip>
          ))}
        </Stack>
        <Typography variant="caption" color="text.disabled">
          Every family widens the pool, so the search has more to sift through. Add one when the
          process plausibly depends on it.
        </Typography>
      </Box>

      <Divider />

      <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" useFlexGap>
        <FormControlLabel
          control={
            <Switch
              size="small"
              checked={config.multiobjective}
              onChange={(event) => set('multiobjective', event.target.checked)}
            />
          }
          label={
            <Tooltip
              title={
                config.multiobjective
                  ? `A Pareto front of candidates traded off between accuracy and ${secondAxis}.`
                  : 'One equation, chosen by accuracy alone. Faster, and it tells you nothing about simpler alternatives.'
              }
            >
              <Typography variant="body2">
                {config.multiobjective ? 'Multi-objective' : 'Single objective'}
              </Typography>
            </Tooltip>
          }
        />
        <TextField
          size="small"
          select
          label="Preprocessor"
          value={config.preprocessor}
          onChange={(event) => set('preprocessor', event.target.value)}
          sx={{ width: 160 }}
          helperText="How derivatives are estimated"
        >
          {capabilities.preprocessors.map((option) => (
            <MenuItem key={option} value={option}>
              {option === 'poly' ? 'Chebyshev polynomials' : option === 'ANN' ? 'Neural network' : option}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          size="small"
          type="number"
          label="Seed"
          value={config.seed ?? ''}
          onChange={(event) => set('seed', event.target.value ? Number(event.target.value) : null)}
          sx={{ width: 120 }}
          helperText="Blank for none"
        />
      </Stack>

      {config.multiobjective && (
        <Grid container spacing={1.5}>
          <Grid size={6}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Sparsity from"
              value={config.sparsity_min}
              onChange={(event) => set('sparsity_min', Number(event.target.value) || 1e-8)}
            />
          </Grid>
          <Grid size={6}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Sparsity to"
              value={config.sparsity_max}
              onChange={(event) => set('sparsity_max', Number(event.target.value) || 1)}
              helperText="The interval the search evolves inside; it decides how many terms survive"
            />
          </Grid>
        </Grid>
      )}

      {nodes > 1_000_000 && (
        <Alert severity="warning" variant="outlined">
          This field has {nodes.toLocaleString()} grid nodes. Derivative preprocessing scales with
          that, so the first generation will take a while before anything appears.
        </Alert>
      )}

      <Button
        variant="contained"
        disabled={busy || (config.variables ?? []).length === 0}
        onClick={() => onStart(config, name || undefined)}
      >
        {busy ? 'Starting…' : 'Start the search'}
      </Button>
    </Stack>
  )
}
