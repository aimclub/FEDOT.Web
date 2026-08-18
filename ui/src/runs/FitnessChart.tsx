import { useMemo, useState } from 'react'
import { useTheme } from '@mui/material/styles'
import Box from '@mui/material/Box'
import Checkbox from '@mui/material/Checkbox'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { GenerationPoint } from '../api/types'

interface Props {
  generations: GenerationPoint[]
  height?: number
}

const fmt = (value: number | null | undefined): string =>
  value === null || value === undefined ? '—' : String(Number(value.toFixed(4)))

interface ChartPoint {
  generation: number
  best: number | null
  mean: number | null
  spread: [number, number] | null
  size: number
  operations: string
  /** The champion of this generation is a different individual than before. */
  leaderChanged: boolean
  /** ...and its structure differs too (not only hyperparameters). */
  structureChanged: boolean
}

/**
 * Fitness across generations.
 *
 * GOLEM minimises internally, so a *lower* value is better; the axis is
 * inverted to keep the familiar "up and to the right means improving" reading.
 *
 * By default only the best-fitness curve is drawn, scaled to its own range —
 * the population spread is an order of magnitude wider and flattens the
 * interesting curve into a straight line (exactly what the checkbox is for).
 * Dots mark the generations where the leading pipeline actually changed.
 */
export default function FitnessChart({ generations, height = 260 }: Props) {
  const theme = useTheme()
  const [showPopulation, setShowPopulation] = useState(false)

  const data = useMemo<ChartPoint[]>(() => {
    let previousUid: string | undefined
    let previousOps: string | undefined
    return generations.map((point) => {
      const uid = point.best_uid ?? null
      const ops = (point.best_operations ?? []).join(' → ')
      // The first generation establishes a leader rather than changing one.
      const leaderChanged = uid !== null && previousUid !== undefined && uid !== previousUid
      const structureChanged = leaderChanged && ops !== previousOps
      if (uid !== null) {
        previousUid = uid
        previousOps = ops
      }
      return {
        generation: point.generation,
        best: point.best_fitness,
        mean: point.mean_fitness,
        spread:
          point.best_fitness !== null && point.worst_fitness !== null
            ? ([point.best_fitness, point.worst_fitness] as [number, number])
            : null,
        size: point.size,
        operations: ops,
        leaderChanged,
        structureChanged,
      }
    })
  }, [generations])

  // In best-only mode the trailing plateau is cut: generations where the best
  // never improved again stretch the axis while showing a flat line.
  const visible = useMemo<ChartPoint[]>(() => {
    if (showPopulation) return data
    let best = Infinity
    let lastImprovement = -1
    data.forEach((point, index) => {
      if (point.best !== null && point.best < best) {
        best = point.best
        lastImprovement = index
      }
    })
    if (lastImprovement < 0) return data
    return data.slice(0, lastImprovement + 1)
  }, [data, showPopulation])
  const hiddenTail = data.length - visible.length

  // In best-only mode the axis hugs the best curve; population mode needs the
  // full range for the band.
  const domain = useMemo<[number | string, number | string]>(() => {
    if (showPopulation) return ['auto', 'auto']
    const values = visible
      .map((point) => point.best)
      .filter((value): value is number => value !== null && Number.isFinite(value))
    if (values.length === 0) return ['auto', 'auto']
    const low = Math.min(...values)
    const high = Math.max(...values)
    const pad = (high - low) * 0.15 || Math.abs(high) * 0.002 || 0.001
    return [low - pad, high + pad]
  }, [visible, showPopulation])

  if (generations.length === 0) {
    return (
      <Box sx={{ height, display: 'grid', placeItems: 'center' }}>
        <Typography variant="body2" color="text.disabled">
          Waiting for the first generation…
        </Typography>
      </Box>
    )
  }

  const changeColor = theme.palette.warning.main

  const renderDot = (props: { cx?: number; cy?: number; payload?: ChartPoint; index?: number }) => {
    const { cx, cy, payload, index } = props
    if (cx === undefined || cy === undefined || !payload) return <g key={index} />
    if (payload.leaderChanged) {
      return (
        <circle
          key={index}
          cx={cx}
          cy={cy}
          r={payload.structureChanged ? 5 : 4}
          fill={changeColor}
          stroke={theme.palette.background.paper}
          strokeWidth={1.5}
        />
      )
    }
    return <circle key={index} cx={cx} cy={cy} r={2} fill={theme.palette.primary.main} />
  }

  const TipContent = ({
    active,
    payload,
  }: {
    active?: boolean
    payload?: { payload: ChartPoint }[]
  }) => {
    if (!active || !payload?.length) return null
    const point = payload[0].payload
    return (
      <Box
        sx={{
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          px: 1.3,
          py: 0.9,
          fontSize: 12,
          maxWidth: 340,
        }}
      >
        <Typography sx={{ fontSize: 12, fontWeight: 700 }}>
          Generation {point.generation}
        </Typography>
        <div>best {fmt(point.best)}</div>
        {showPopulation && point.mean !== null && <div>mean {fmt(point.mean)}</div>}
        {showPopulation && point.spread && (
          <div>
            range {fmt(point.spread[0])} … {fmt(point.spread[1])} over {point.size}
          </div>
        )}
        {point.operations && (
          <Typography sx={{ fontSize: 11, color: 'text.secondary', mt: 0.4 }}>
            {point.operations}
          </Typography>
        )}
        {point.leaderChanged && (
          <Typography sx={{ fontSize: 11, color: changeColor, mt: 0.2 }}>
            {point.structureChanged
              ? 'new best pipeline (structure changed)'
              : 'new best pipeline (same structure, other hyperparameters)'}
          </Typography>
        )}
      </Box>
    )
  }

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.25 }}>
        <Typography variant="caption" color="text.secondary" sx={{ flexGrow: 1 }}>
          Lower is better, so the axis is inverted.{' '}
          <Box component="span" sx={{ color: changeColor }}>
            ●
          </Box>{' '}
          marks a change of the leading pipeline.
          {hiddenTail > 0 && ` ${hiddenTail} trailing generations without improvement are hidden.`}
        </Typography>
        <Tooltip title="Also draw the population mean and the best-worst band. The band is far wider than the best curve, so the axis zooms out with it.">
          <FormControlLabel
            sx={{ mr: 0 }}
            control={
              <Checkbox
                size="small"
                checked={showPopulation}
                onChange={(event) => setShowPopulation(event.target.checked)}
              />
            }
            label={
              <Typography variant="caption" color="text.secondary">
                population mean &amp; spread
              </Typography>
            }
          />
        </Tooltip>
      </Stack>

      <Box sx={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={visible} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
            <CartesianGrid stroke={theme.palette.divider} strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="generation"
              tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
              stroke={theme.palette.divider}
              label={{
                value: 'generation',
                position: 'insideBottom',
                offset: -2,
                fill: theme.palette.text.disabled,
                fontSize: 11,
              }}
            />
            <YAxis
              reversed
              tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
              stroke={theme.palette.divider}
              width={68}
              domain={domain as [number, number]}
              tickFormatter={(value: number) =>
                Math.abs(value) >= 1000 || (Math.abs(value) < 0.01 && value !== 0)
                  ? value.toExponential(1)
                  : String(Number(value.toFixed(4)))
              }
            />
            <ChartTooltip content={<TipContent />} />
            {showPopulation && (
              <Area
                dataKey="spread"
                stroke="none"
                fill={theme.palette.primary.main}
                fillOpacity={0.11}
                isAnimationActive={false}
                connectNulls
              />
            )}
            {showPopulation && (
              <Line
                type="monotone"
                dataKey="mean"
                stroke={theme.palette.text.disabled}
                strokeWidth={1.2}
                strokeDasharray="4 3"
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            )}
            <Line
              type="monotone"
              dataKey="best"
              stroke={theme.palette.primary.main}
              strokeWidth={2.2}
              dot={renderDot}
              isAnimationActive={false}
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  )
}
