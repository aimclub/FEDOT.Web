import { useEffect, useMemo, useRef } from 'react'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { useTheme } from '@mui/material/styles'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { DatasetPreview } from '../api/types'

/**
 * A picture of the field before a search is started on it.
 *
 * It is not decoration. EPDE differentiates with respect to the coordinates it
 * is given, so a field uploaded with the wrong axis order, an upside-down time
 * axis or a grid that is coarse where the dynamics are is a run that will waste
 * minutes producing an equation about the wrong thing. One look at the field
 * catches all three.
 *
 * A 2-D field is drawn on a canvas rather than as SVG: the payload is already
 * downsampled to at most 160 points a side, and 25 000 SVG rectangles is not
 * something to hand a browser when a single `putImageData` will do.
 */

interface Props {
  preview: DatasetPreview
  height?: number
}

export default function FieldPreview({ preview, height = 260 }: Props) {
  if (preview.kind === 'series') {
    return <SeriesPreview preview={preview} height={height} />
  }
  return <SurfacePreview preview={preview} height={height} />
}

function SeriesPreview({ preview, height }: Props) {
  const theme = useTheme()
  const palette = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
  ]

  const data = useMemo(() => {
    const x = preview.x ?? []
    return x.map((value, index) => {
      const row: Record<string, number | null> = { x: value }
      for (const series of preview.series ?? []) {
        row[series.name] = series.values[index] ?? null
      }
      return row
    })
  }, [preview])

  return (
    <Box sx={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -12 }}>
          <CartesianGrid stroke={theme.palette.divider} strokeDasharray="3 3" />
          <XAxis
            dataKey="x"
            tick={{ fontSize: 11 }}
            stroke={theme.palette.text.disabled}
            tickFormatter={(value: number) => Number(value.toPrecision(3)).toString()}
          />
          <YAxis tick={{ fontSize: 11 }} stroke={theme.palette.text.disabled} width={56} />
          <Tooltip
            contentStyle={{
              background: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 8,
              fontSize: '0.78rem',
            }}
          />
          {(preview.series ?? []).map((series, index) => (
            <Line
              key={series.name}
              type="monotone"
              dataKey={series.name}
              stroke={palette[index % palette.length]}
              dot={false}
              strokeWidth={1.6}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Box>
  )
}

/** Blue → white → red, so zero reads as neutral and sign is visible. */
function colourFor(value: number, min: number, max: number): [number, number, number] {
  const span = max - min || 1
  const t = Math.min(1, Math.max(0, (value - min) / span))
  if (t < 0.5) {
    const k = t * 2
    return [Math.round(40 + 215 * k), Math.round(90 + 165 * k), 255]
  }
  const k = (t - 0.5) * 2
  return [255, Math.round(255 - 165 * k), Math.round(255 - 215 * k)]
}

function SurfacePreview({ preview, height }: Props) {
  const theme = useTheme()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const surface = preview.surfaces?.[0]

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !surface) return
    const rows = surface.values.length
    const columns = surface.values[0]?.length ?? 0
    if (!rows || !columns) return

    canvas.width = columns
    canvas.height = rows
    const context = canvas.getContext('2d')
    if (!context) return

    const image = context.createImageData(columns, rows)
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const value = surface.values[row][column]
        const offset = (row * columns + column) * 4
        if (value === null) {
          // A gap in the field is not a value; showing it as one would put a
          // colour where there is no measurement.
          image.data.set([128, 128, 128, 40], offset)
          continue
        }
        const [r, g, b] = colourFor(value, surface.min, surface.max)
        image.data.set([r, g, b, 255], offset)
      }
    }
    context.putImageData(image, 0, 0)
  }, [surface])

  if (!surface) {
    return (
      <Typography variant="body2" color="text.disabled">
        This field has nothing to draw.
      </Typography>
    )
  }

  const [rowAxis, columnAxis] = preview.axes

  return (
    <Stack spacing={0.75}>
      <Stack direction="row" spacing={1} alignItems="stretch" sx={{ height }}>
        <Stack justifyContent="space-between" sx={{ py: 0.5 }}>
          <Typography variant="caption" color="text.disabled">
            {rowAxis?.stop.toPrecision(3)}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', alignSelf: 'center' }}
          >
            {rowAxis?.name}
          </Typography>
          <Typography variant="caption" color="text.disabled">
            {rowAxis?.start.toPrecision(3)}
          </Typography>
        </Stack>
        <Box
          sx={{
            flexGrow: 1,
            minWidth: 0,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            overflow: 'hidden',
          }}
        >
          <Box
            component="canvas"
            ref={canvasRef}
            sx={{
              width: '100%',
              height: '100%',
              display: 'block',
              // The field is a grid of samples; smoothing it would suggest a
              // resolution the data does not have.
              imageRendering: 'pixelated',
              // Row 0 is drawn at the top, but an axis reads upwards.
              transform: 'scaleY(-1)',
            }}
          />
        </Box>
      </Stack>

      <Stack direction="row" justifyContent="space-between" sx={{ pl: 4 }}>
        <Typography variant="caption" color="text.disabled">
          {columnAxis?.start.toPrecision(3)}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {columnAxis?.name}
        </Typography>
        <Typography variant="caption" color="text.disabled">
          {columnAxis?.stop.toPrecision(3)}
        </Typography>
      </Stack>

      <Stack direction="row" spacing={1} alignItems="center" sx={{ pl: 4 }}>
        <Typography variant="caption" color="text.disabled">
          {surface.name}: {surface.min.toPrecision(3)}
        </Typography>
        <Box
          sx={{
            flexGrow: 1,
            height: 8,
            borderRadius: 4,
            border: '1px solid',
            borderColor: theme.palette.divider,
            background: 'linear-gradient(to right, rgb(40,90,255), rgb(255,255,255), rgb(255,90,40))',
          }}
        />
        <Typography variant="caption" color="text.disabled">
          {surface.max.toPrecision(3)}
        </Typography>
      </Stack>

      {Object.keys(preview.fixed).length > 0 && (
        <Typography variant="caption" color="text.disabled" sx={{ pl: 4 }}>
          Other axes fixed at{' '}
          {Object.entries(preview.fixed)
            .map(([name, index]) => `${name}[${index}]`)
            .join(', ')}
        </Typography>
      )}
    </Stack>
  )
}
