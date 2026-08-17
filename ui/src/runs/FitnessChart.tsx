import { useTheme } from '@mui/material/styles'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { GenerationPoint } from '../api/types'

interface Props {
  generations: GenerationPoint[]
  height?: number
}

/**
 * Fitness across generations.
 *
 * GOLEM minimises internally, so a *lower* value is better; the axis is
 * inverted to keep the familiar "up and to the right means improving" reading.
 */
export default function FitnessChart({ generations, height = 260 }: Props) {
  const theme = useTheme()

  if (generations.length === 0) {
    return (
      <Box sx={{ height, display: 'grid', placeItems: 'center' }}>
        <Typography variant="body2" color="text.disabled">
          Waiting for the first generation…
        </Typography>
      </Box>
    )
  }

  const data = generations.map((point) => ({
    generation: point.generation,
    best: point.best_fitness,
    mean: point.mean_fitness,
    worst: point.worst_fitness,
    // The band between best and worst shows how converged the population is.
    spread:
      point.best_fitness !== null && point.worst_fitness !== null
        ? [point.best_fitness, point.worst_fitness]
        : null,
    size: point.size,
  }))

  return (
    <Box sx={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
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
            width={62}
            domain={['auto', 'auto']}
            tickFormatter={(value: number) =>
              Math.abs(value) >= 1000 || (Math.abs(value) < 0.01 && value !== 0)
                ? value.toExponential(1)
                : String(Number(value.toFixed(4)))
            }
          />
          <Tooltip
            contentStyle={{
              background: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(label) => `Generation ${label}`}
            formatter={(value: unknown, key: string) => {
              if (Array.isArray(value)) {
                const [low, high] = value as [number, number]
                return [`${Number(low.toFixed(4))} … ${Number(high.toFixed(4))}`, 'population range']
              }
              return [typeof value === 'number' ? Number(value.toFixed(4)) : String(value), key]
            }}
          />
          <Area
            dataKey="spread"
            stroke="none"
            fill={theme.palette.primary.main}
            fillOpacity={0.11}
            isAnimationActive={false}
            connectNulls
          />
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
          <Line
            type="monotone"
            dataKey="best"
            stroke={theme.palette.primary.main}
            strokeWidth={2.2}
            dot={{ r: 2.5 }}
            isAnimationActive={false}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  )
}
