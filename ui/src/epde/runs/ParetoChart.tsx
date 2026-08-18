import { useMemo } from 'react'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'

import type { ParetoPoint } from '../api/types'

/**
 * The trade-off the search is actually exploring.
 *
 * A multi-objective run does not return an answer; it returns a set of
 * answers, none of which is better than another on both counts. Showing only
 * the most accurate one would hide the point of running MOEA/D at all — often
 * the interesting candidate is the one a little worse and much simpler, because
 * that is the one that looks like physics.
 *
 * Both axes are minimised, so the useful corner is the bottom left.
 */

interface Props {
  front: ParetoPoint[]
  objectiveNames: string[]
  selectedUid?: string | null
  onSelect?: (uid: string) => void
  height?: number
}

export default function ParetoChart({
  front,
  objectiveNames,
  selectedUid,
  onSelect,
  height = 260,
}: Props) {
  const theme = useTheme()

  const points = useMemo(
    () =>
      front
        .filter((point) => point.objectives.length >= 2)
        .map((point) => ({
          uid: point.uid,
          x: point.objectives[0],
          y: point.objectives[1],
          text: point.text,
          terms: point.active_terms,
        })),
    [front],
  )

  if (points.length === 0) {
    return (
      <Stack sx={{ height }} alignItems="center" justifyContent="center" px={3}>
        <Typography variant="body2" color="text.disabled" textAlign="center">
          {front.length > 0
            ? 'This run optimised a single objective, so there is no front to trade off along.'
            : 'The front appears once the first generation has been evaluated.'}
        </Typography>
      </Stack>
    )
  }

  return (
    <Box sx={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 12, right: 20, bottom: 24, left: -8 }}>
          <CartesianGrid stroke={theme.palette.divider} strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="x"
            name={objectiveNames[0] ?? 'objective 0'}
            tick={{ fontSize: 11 }}
            stroke={theme.palette.text.disabled}
            label={{
              value: `${objectiveNames[0] ?? 'objective 0'} →  worse`,
              position: 'insideBottom',
              offset: -14,
              style: { fontSize: 11, fill: theme.palette.text.disabled },
            }}
            tickFormatter={(value: number) => Number(value.toPrecision(3)).toString()}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={objectiveNames[1] ?? 'objective 1'}
            tick={{ fontSize: 11 }}
            stroke={theme.palette.text.disabled}
            width={64}
            tickFormatter={(value: number) => Number(value.toPrecision(3)).toString()}
          />
          <ZAxis range={[70, 70]} />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ payload }) => {
              const point = payload?.[0]?.payload as (typeof points)[number] | undefined
              if (!point) return null
              return (
                <Box
                  sx={{
                    p: 1,
                    maxWidth: 360,
                    background: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 1,
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{ fontFamily: '"JetBrains Mono", monospace', whiteSpace: 'pre-wrap' }}
                  >
                    {point.text}
                  </Typography>
                  <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }} color="text.secondary">
                    {objectiveNames[0] ?? 'objective 0'} {Number(point.x.toPrecision(4))} ·{' '}
                    {objectiveNames[1] ?? 'objective 1'} {Number(point.y.toPrecision(4))} ·{' '}
                    {point.terms} terms
                  </Typography>
                </Box>
              )
            }}
          />
          <Scatter
            data={points}
            onClick={(entry) => onSelect?.((entry as unknown as { uid: string }).uid)}
            cursor={onSelect ? 'pointer' : undefined}
          >
            {points.map((point) => (
              <Cell
                key={point.uid}
                fill={
                  point.uid === selectedUid
                    ? theme.palette.success.main
                    : alpha(theme.palette.primary.main, 0.75)
                }
                stroke={point.uid === selectedUid ? theme.palette.success.dark : undefined}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </Box>
  )
}
