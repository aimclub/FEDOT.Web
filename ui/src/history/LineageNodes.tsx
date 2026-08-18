import { Handle, Position, type Node, type NodeProps } from '@xyflow/react'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import EmojiEventsRoundedIcon from '@mui/icons-material/EmojiEventsRounded'
import StarRoundedIcon from '@mui/icons-material/StarRounded'

/** Colours for the evolutionary operators, reused by the legend. */
export const OPERATOR_COLORS: Record<string, string> = {
  mutation: '#f59e0b',
  crossover: '#8b5cf6',
  selection: '#94a3b8',
}

export const operatorColor = (type?: string | null): string =>
  (type && OPERATOR_COLORS[type]) || '#94a3b8'

export interface IndividualNodeData extends Record<string, unknown> {
  uid: string
  generation: number
  fitness: number | null
  operations: string[]
  isBest: boolean
  /** The run's returned pipeline; only a finished run has one. */
  isFinal: boolean
  /** The leader so far, while the run is still going. */
  isCurrentBest: boolean
  onWinningPath: boolean
  /** Position of this individual's fitness within the run, 0 = worst, 1 = best. */
  rank: number
  selected: boolean
}

export interface OperatorNodeData extends Record<string, unknown> {
  operatorType: string
  label: string
  onWinningPath: boolean
  /** Operation lists of the pipelines this operator consumed. */
  parentOps: string[][]
  /** Operation list of the pipeline it produced, when known. */
  childOps: string[] | null
}

export type IndividualFlowNode = Node<IndividualNodeData, 'lineageIndividual'>
export type OperatorFlowNode = Node<OperatorNodeData, 'lineageOperator'>

const formatFitness = (value: number | null): string => {
  if (value === null || value === undefined) return 'not evaluated'
  return Number(value.toFixed(4)).toString()
}

/**
 * One pipeline, at one point in the evolution.
 *
 * Fill intensity tracks fitness relative to the rest of the run, so the graph
 * shows where quality is concentrated before any node is clicked.
 */
export function LineageIndividualNode({ data }: NodeProps<IndividualFlowNode>) {
  const theme = useTheme()
  const isLeader = data.isFinal || data.isCurrentBest
  const accent = isLeader
    ? theme.palette.success.main
    : data.onWinningPath
      ? theme.palette.primary.main
      : theme.palette.text.disabled

  const intensity = Number.isFinite(data.rank) ? 0.08 + data.rank * 0.26 : 0.08

  return (
    <Tooltip
      placement="right"
      title={
        <Box>
          <div>fitness {formatFitness(data.fitness)}</div>
          <div>generation {data.generation}</div>
          <div>{data.operations.join(' → ') || 'empty pipeline'}</div>
          <div style={{ opacity: 0.7, marginTop: 4 }}>click to open the pipeline</div>
        </Box>
      }
    >
      <Box
        sx={{
          width: '100%',
          height: '100%',
          px: 0.9,
          py: 0.5,
          borderRadius: 1.5,
          cursor: 'pointer',
          bgcolor: alpha(accent, intensity),
          border: '1px solid',
          borderColor: data.selected ? accent : alpha(accent, 0.45),
          boxShadow: data.selected ? `0 0 0 2px ${alpha(accent, 0.4)}` : 'none',
          opacity: data.onWinningPath ? 1 : 0.55,
          overflow: 'hidden',
        }}
      >
        <Handle type="target" position={Position.Top} style={{ opacity: 0, width: 1, height: 1 }} />

        <Stack direction="row" alignItems="center" spacing={0.4}>
          <Typography
            sx={{ fontSize: '0.72rem', fontWeight: 700, fontFamily: '"JetBrains Mono", monospace' }}
          >
            {formatFitness(data.fitness)}
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          {data.isBest && (
            <StarRoundedIcon sx={{ fontSize: 13, color: accent }} titleAccess="best in generation" />
          )}
          {isLeader && (
            <EmojiEventsRoundedIcon
              sx={{ fontSize: 13, color: theme.palette.success.main }}
              titleAccess={data.isFinal ? 'final choice' : 'best so far'}
            />
          )}
        </Stack>

        <Typography
          noWrap
          sx={{
            fontSize: '0.62rem',
            color: 'text.secondary',
            fontFamily: '"JetBrains Mono", monospace',
          }}
        >
          {data.operations.join(' ') || '—'}
        </Typography>
        <Typography sx={{ fontSize: '0.58rem', color: 'text.disabled' }}>
          {data.operations.length} node{data.operations.length === 1 ? '' : 's'}
        </Typography>

        <Handle type="source" position={Position.Bottom} style={{ opacity: 0, width: 1, height: 1 }} />
      </Box>
    </Tooltip>
  )
}

/** Multiset difference: items of `left` not covered by `right`. */
const missingFrom = (left: string[], right: string[]): string[] => {
  const counts = new Map<string, number>()
  for (const item of right) counts.set(item, (counts.get(item) ?? 0) + 1)
  const result: string[] = []
  for (const item of left) {
    const available = counts.get(item) ?? 0
    if (available > 0) counts.set(item, available - 1)
    else result.push(item)
  }
  return result
}

/** What one application of the operator actually did, for the hover card. */
function describeChange(data: OperatorNodeData): { text: string; dim?: boolean }[] {
  const child = data.childOps
  const lines: { text: string; dim?: boolean }[] = []

  for (const parent of data.parentOps) {
    lines.push({ text: `from: ${parent.join(' → ') || '—'}` })
  }
  if (data.parentOps.length === 0) {
    lines.push({ text: 'applied to the previous operator’s result', dim: true })
  }
  if (child) {
    lines.push({ text: `to:   ${child.join(' → ')}` })
  }

  // A structural diff is only unambiguous with a single parent; a crossover
  // recombines, so its parents and child are simply listed side by side.
  if (child && data.parentOps.length === 1) {
    const added = missingFrom(child, data.parentOps[0])
    const removed = missingFrom(data.parentOps[0], child)
    if (added.length || removed.length) {
      lines.push({
        text: [...added.map((op) => `+ ${op}`), ...removed.map((op) => `− ${op}`)].join('   '),
      })
    } else {
      lines.push({ text: 'same structure — hyperparameters changed', dim: true })
    }
  }
  return lines
}

/** A mutation or crossover, drawn as the junction it is. */
export function LineageOperatorNode({ data }: NodeProps<OperatorFlowNode>) {
  const color = operatorColor(data.operatorType)
  const initial = (data.operatorType?.[0] ?? '?').toUpperCase()
  const change = describeChange(data)

  return (
    <Tooltip
      placement="right"
      title={
        <Box sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.72rem' }}>
          <Box sx={{ fontWeight: 700, fontFamily: 'inherit' }}>
            {data.operatorType}
            {data.label && data.label !== data.operatorType ? ` — ${data.label}` : ''}
          </Box>
          {change.map((line, index) => (
            <Box key={index} sx={{ opacity: line.dim ? 0.65 : 1, whiteSpace: 'pre-wrap' }}>
              {line.text}
            </Box>
          ))}
        </Box>
      }
    >
      <Box
        sx={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          display: 'grid',
          placeItems: 'center',
          bgcolor: alpha(color, 0.22),
          border: '1.5px solid',
          borderColor: color,
          opacity: data.onWinningPath ? 1 : 0.5,
        }}
      >
        <Handle type="target" position={Position.Top} style={{ opacity: 0, width: 1, height: 1 }} />
        <Typography sx={{ fontSize: '0.72rem', fontWeight: 800, color }}>{initial}</Typography>
        <Handle type="source" position={Position.Bottom} style={{ opacity: 0, width: 1, height: 1 }} />
      </Box>
    </Tooltip>
  )
}
