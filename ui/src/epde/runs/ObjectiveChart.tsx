import { useMemo } from 'react'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { useTheme } from '@mui/material/styles'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { GenerationPoint } from '../api/types'

/**
 * How the search moved, generation by generation.
 *
 * Two curves, because the two questions are different. The best value of each
 * objective says how far each axis has come — but a multi-objective search can
 * improve without either extreme moving, by filling in the middle of the front.
 * The dominated hypervolume catches that: it is one number that only goes up as
 * the front advances, measured against a reference fixed at the first
 * generation so it stays comparable across the run.
 */

interface Props {
  generations: GenerationPoint[]
  objectiveNames: string[]
  height?: number
}

export default function ObjectiveChart({ generations, objectiveNames, height = 240 }: Props) {
  const theme = useTheme()

  const data = useMemo(
    () =>
      generations.map((point) => {
        const row: Record<string, number | string | null> = {
          generation: point.label || `gen ${point.generation}`,
          hypervolume: point.hypervolume,
        }
        for (const objective of point.objectives) {
          row[`best:${objective.index}`] = objective.best
        }
        return row
      }),
    [generations],
  )

  const palette = [theme.palette.primary.main, theme.palette.secondary.main, theme.palette.warning.main]
  const names = objectiveNames.length
    ? objectiveNames
    : (generations[0]?.objectives ?? []).map((objective) => objective.name)

  if (generations.length === 0) {
    return (
      <Stack sx={{ height }} alignItems="center" justifyContent="center">
        <Typography variant="body2" color="text.disabled">
          Waiting for the first generation…
        </Typography>
      </Stack>
    )
  }

  const hasHypervolume = data.some((row) => typeof row.hypervolume === 'number')

  return (
    <Box sx={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: -14 }}>
          <CartesianGrid stroke={theme.palette.divider} strokeDasharray="3 3" />
          <XAxis dataKey="generation" tick={{ fontSize: 11 }} stroke={theme.palette.text.disabled} />
          <YAxis
            yAxisId="objective"
            tick={{ fontSize: 11 }}
            stroke={theme.palette.text.disabled}
            width={64}
            tickFormatter={(value: number) => Number(value.toPrecision(3)).toString()}
          />
          {hasHypervolume && (
            <YAxis
              yAxisId="volume"
              orientation="right"
              tick={{ fontSize: 11 }}
              stroke={theme.palette.text.disabled}
              width={56}
              tickFormatter={(value: number) => Number(value.toPrecision(2)).toString()}
            />
          )}
          <Tooltip
            contentStyle={{
              background: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 8,
              fontSize: '0.78rem',
            }}
            formatter={(value: number) => Number(value.toPrecision(4))}
          />
          <Legend wrapperStyle={{ fontSize: '0.72rem' }} />
          {names.map((name, index) => (
            <Line
              key={name}
              yAxisId="objective"
              type="monotone"
              dataKey={`best:${index}`}
              name={`best ${name}`}
              stroke={palette[index % palette.length]}
              dot={false}
              strokeWidth={1.8}
              isAnimationActive={false}
            />
          ))}
          {hasHypervolume && (
            <Line
              yAxisId="volume"
              type="monotone"
              dataKey="hypervolume"
              name="front coverage"
              stroke={theme.palette.success.main}
              strokeDasharray="4 3"
              dot={false}
              strokeWidth={1.4}
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </Box>
  )
}
