import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import InputAdornment from '@mui/material/InputAdornment'
import MenuItem from '@mui/material/MenuItem'
import Slider from '@mui/material/Slider'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import RestartAltRoundedIcon from '@mui/icons-material/RestartAltRounded'
import TuneRoundedIcon from '@mui/icons-material/TuneRounded'

import type { ParameterSchema } from '../api/types'
import { describeScope, formatParamValue } from './paramDisplay'

interface Props {
  schema: ParameterSchema
  value: unknown
  isSet: boolean
  onChange: (value: unknown) => void
  onReset: () => void
  disabled?: boolean
}

/** Map a value onto a 0–100 slider position, honouring logarithmic scopes. */
const toSliderPosition = (value: number, min: number, max: number, log: boolean): number => {
  if (log && min > 0 && max > 0) {
    const ratio = (Math.log(value) - Math.log(min)) / (Math.log(max) - Math.log(min))
    return Math.min(100, Math.max(0, ratio * 100))
  }
  return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100))
}

const fromSliderPosition = (position: number, min: number, max: number, log: boolean): number => {
  if (log && min > 0 && max > 0) {
    return Math.exp(Math.log(min) + (position / 100) * (Math.log(max) - Math.log(min)))
  }
  return min + (position / 100) * (max - min)
}

const roundForType = (value: number, integer: boolean): number =>
  integer ? Math.round(value) : Number(value.toPrecision(6))

/**
 * One hyperparameter, rendered according to the schema FEDOT publishes for it.
 *
 * The widget is chosen from `type`: a bounded slider for continuous and discrete
 * parameters, a dropdown for categorical ones, a switch for booleans. The
 * sampling scope shown next to the control is the same range the FEDOT tuner
 * would search, so a value typed here can be compared against what evolution
 * would consider.
 */
export default function HyperparameterField({
  schema,
  value,
  isSet,
  onChange,
  onReset,
  disabled,
}: Props) {
  const theme = useTheme()
  const scope = describeScope(schema)
  const bounded = schema.minimum !== null && schema.maximum !== null
  const isInteger = schema.value_type === 'integer' || schema.type === 'discrete'

  // A local copy keeps typing responsive while the slider stays in sync.
  const [draft, setDraft] = useState<string>(value === null || value === undefined ? '' : String(value))
  useEffect(() => {
    setDraft(value === null || value === undefined ? '' : String(value))
  }, [value])

  const commitNumber = (raw: string) => {
    setDraft(raw)
    if (raw.trim() === '') return
    const parsed = Number(raw)
    if (Number.isNaN(parsed)) return
    onChange(isInteger ? Math.round(parsed) : parsed)
  }

  const label = (
    <Stack direction="row" alignItems="center" spacing={0.6} sx={{ minWidth: 0 }}>
      <Typography
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '0.79rem',
          fontWeight: isSet ? 700 : 500,
          color: isSet ? 'primary.main' : 'text.primary',
        }}
      >
        {schema.name}
      </Typography>

      {schema.tunable && (
        <Tooltip
          title={`Explored by the FEDOT tuner${schema.distribution ? ` (${schema.distribution})` : ''}`}
        >
          <TuneRoundedIcon sx={{ fontSize: 13, color: 'text.disabled' }} />
        </Tooltip>
      )}

      <Box sx={{ flexGrow: 1 }} />

      {scope && (
        <Typography sx={{ fontSize: '0.68rem', color: 'text.disabled', whiteSpace: 'nowrap' }}>
          {scope}
        </Typography>
      )}

      {isSet && schema.default !== null && schema.default !== undefined && (
        <Tooltip title={`Reset to the FEDOT default (${formatParamValue(schema.default)})`}>
          <IconButton size="small" onClick={onReset} disabled={disabled} sx={{ p: 0.2 }}>
            <RestartAltRoundedIcon sx={{ fontSize: 15 }} />
          </IconButton>
        </Tooltip>
      )}
    </Stack>
  )

  let control: React.ReactNode

  if (schema.type === 'nested' && schema.nested_variants?.length) {
    const current = (value ?? {}) as Record<string, unknown>
    const activeVariant =
      schema.nested_variants.find((variant) =>
        Object.entries(variant.fixed).every(([key, fixed]) => current[key] === fixed),
      ) ?? schema.nested_variants[0]

    control = (
      <Stack spacing={0.8}>
        <TextField
          select
          size="small"
          value={activeVariant.label}
          disabled={disabled}
          onChange={(event) => {
            const variant = schema.nested_variants!.find((item) => item.label === event.target.value)
            if (!variant) return
            const next: Record<string, unknown> = { ...variant.fixed }
            for (const [key, options] of Object.entries(variant.options)) {
              next[key] = options[0]
            }
            onChange(next)
          }}
        >
          {schema.nested_variants.map((variant) => (
            <MenuItem key={variant.label} value={variant.label}>
              {variant.label}
            </MenuItem>
          ))}
        </TextField>

        {Object.entries(activeVariant.options).map(([key, options]) => (
          <TextField
            key={key}
            select
            size="small"
            label={key}
            value={String(current[key] ?? options[0])}
            disabled={disabled}
            onChange={(event) => onChange({ ...current, [key]: event.target.value })}
          >
            {options.map((option) => (
              <MenuItem key={String(option)} value={String(option)}>
                {String(option)}
              </MenuItem>
            ))}
          </TextField>
        ))}
      </Stack>
    )
  } else if (schema.value_type === 'boolean' && (!schema.choices || schema.choices.length <= 2)) {
    control = (
      <Stack direction="row" alignItems="center" spacing={1}>
        <Switch
          size="small"
          checked={value === true}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
        />
        <Typography sx={{ fontSize: '0.78rem', color: 'text.secondary' }}>
          {value === true ? 'true' : 'false'}
        </Typography>
      </Stack>
    )
  } else if (schema.choices && schema.choices.length > 0) {
    const asString = value === null || value === undefined ? '' : String(value)
    control = (
      <TextField
        select
        size="small"
        fullWidth
        value={schema.choices.some((choice) => String(choice) === asString) ? asString : ''}
        disabled={disabled}
        onChange={(event) => {
          const chosen = schema.choices!.find((choice) => String(choice) === event.target.value)
          onChange(chosen ?? event.target.value)
        }}
      >
        {schema.choices.map((choice) => (
          <MenuItem key={String(choice)} value={String(choice)}>
            {String(choice)}
          </MenuItem>
        ))}
      </TextField>
    )
  } else if (bounded && (schema.type === 'continuous' || schema.type === 'discrete')) {
    const min = schema.minimum!
    const max = schema.maximum!
    // An empty field means "not set", which is not the same as zero — without
    // this check every parameter that has no default reads as out of scope.
    const hasValue = typeof value === 'number' || draft.trim() !== ''
    const numeric = typeof value === 'number' ? value : Number(draft)
    const valid = hasValue && Number.isFinite(numeric)
    const outOfScope = valid && (numeric < min || numeric > max)

    control = (
      <Stack direction="row" spacing={1.5} alignItems="center">
        <Slider
          size="small"
          disabled={disabled}
          value={valid ? toSliderPosition(numeric, min, max, schema.log_scale) : 0}
          min={0}
          max={100}
          step={0.1}
          onChange={(_, position) =>
            onChange(
              roundForType(
                fromSliderPosition(position as number, min, max, schema.log_scale),
                isInteger,
              ),
            )
          }
          sx={{ flexGrow: 1 }}
        />
        <TextField
          size="small"
          value={draft}
          disabled={disabled}
          onChange={(event) => commitNumber(event.target.value)}
          error={outOfScope}
          helperText={outOfScope ? 'outside the tuner scope' : undefined}
          sx={{ width: 118 }}
          slotProps={{
            input: {
              endAdornment: schema.log_scale ? (
                <InputAdornment position="end">
                  <Tooltip title="This parameter is searched on a logarithmic scale">
                    <Typography sx={{ fontSize: '0.6rem', color: 'text.disabled' }}>log</Typography>
                  </Tooltip>
                </InputAdornment>
              ) : undefined,
            },
          }}
        />
      </Stack>
    )
  } else {
    control = (
      <TextField
        size="small"
        fullWidth
        value={draft}
        disabled={disabled}
        onChange={(event) => {
          setDraft(event.target.value)
          if (schema.value_type === 'number' || schema.value_type === 'integer') {
            commitNumber(event.target.value)
          } else {
            onChange(event.target.value)
          }
        }}
      />
    )
  }

  return (
    <Box
      sx={{
        px: 1.25,
        py: 0.9,
        borderRadius: 1.5,
        border: '1px solid',
        borderColor: isSet ? alpha(theme.palette.primary.main, 0.35) : 'transparent',
        bgcolor: isSet ? alpha(theme.palette.primary.main, 0.05) : 'transparent',
        '&:hover': { bgcolor: alpha(theme.palette.action.hover, 0.5) },
      }}
    >
      {label}
      <Box sx={{ mt: 0.6 }}>{control}</Box>
      {schema.default !== null && schema.default !== undefined && (
        <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }} alignItems="center">
          <Typography sx={{ fontSize: '0.66rem', color: 'text.disabled' }}>default</Typography>
          <Chip
            size="small"
            variant="outlined"
            label={formatParamValue(schema.default)}
            sx={{ height: 16, fontSize: '0.62rem', '& .MuiChip-label': { px: 0.6 } }}
          />
        </Stack>
      )}
    </Box>
  )
}
