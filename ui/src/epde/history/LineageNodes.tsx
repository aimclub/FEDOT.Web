import { Handle, Position } from '@xyflow/react'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import CallSplitRoundedIcon from '@mui/icons-material/CallSplitRounded'
import ContentCopyRoundedIcon from '@mui/icons-material/ContentCopyRounded'
import ShuffleRoundedIcon from '@mui/icons-material/ShuffleRounded'

/**
 * The two node kinds of the genealogy.
 *
 * A candidate card carries the terms of its equation rather than a fitness
 * number, because that is what tells one candidate from another at a glance —
 * and because in a multi-objective run there is no single number to show. Front
 * membership takes the place of "best of this generation".
 */

export const OPERATOR_COLORS: Record<string, string> = {
  mutation: '#e0a34a',
  crossover: '#5aa9e6',
  copy: '#9e9e9e',
}

export const operatorColor = (type?: string | null): string =>
  (type && OPERATOR_COLORS[type]) || '#8e8e8e'

interface IndividualData {
  uid: string
  generation: number
  objectives: number[] | null
  objectiveNames: string[]
  paretoRank: number | null
  terms: string[]
  isOnFront: boolean
  isFinal: boolean
  isCurrentBest: boolean
  onWinningPath: boolean
  /** 0 (worst seen) … 1 (best seen) on the first objective, for the fill. */
  rank: number
  selected: boolean
}

export function LineageIndividualNode({ data }: { data: IndividualData }) {
  const theme = useTheme()
  const leading = data.isFinal || data.isCurrentBest
  const accent = leading
    ? theme.palette.success.main
    : data.isOnFront
      ? theme.palette.primary.main
      : theme.palette.text.disabled

  const objectives = data.objectives ?? []
  const summary = objectives
    .map((value, index) => `${data.objectiveNames[index] ?? `objective ${index}`}: ${Number(value.toPrecision(4))}`)
    .join('\n')

  return (
    <Tooltip
      title={
        <Box sx={{ whiteSpace: 'pre-line' }}>
          {summary || 'This candidate was never evaluated.'}
          {data.paretoRank !== null && `\nnon-domination level ${data.paretoRank}`}
          {data.terms.length > 0 && `\n\n${data.terms.join('  ·  ')}`}
        </Box>
      }
    >
      <Box
        sx={{
          width: '100%',
          height: '100%',
          px: 1,
          py: 0.6,
          borderRadius: 1.25,
          border: '1.5px solid',
          borderColor: data.selected ? theme.palette.warning.main : accent,
          bgcolor: alpha(accent, 0.05 + 0.22 * data.rank),
          opacity: data.onWinningPath ? 1 : 0.55,
          overflow: 'hidden',
          cursor: 'pointer',
          boxShadow: data.selected ? `0 0 0 3px ${alpha(theme.palette.warning.main, 0.3)}` : undefined,
        }}
      >
        <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Typography
            sx={{
              fontSize: '0.62rem',
              fontFamily: '"JetBrains Mono", monospace',
              color: 'text.disabled',
            }}
          >
            {data.uid}
          </Typography>
          {leading && (
            <Typography sx={{ fontSize: '0.6rem', color: theme.palette.success.main, fontWeight: 700 }}>
              {data.isFinal ? 'front' : 'leading'}
            </Typography>
          )}
        </Stack>
        <Typography
          sx={{
            fontSize: '0.68rem',
            fontFamily: '"JetBrains Mono", monospace',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {data.terms[0] ?? '—'}
        </Typography>
        <Typography sx={{ fontSize: '0.6rem', color: 'text.secondary' }}>
          {objectives.length > 0
            ? objectives.map((value) => Number(value.toPrecision(3))).join(' / ')
            : 'not evaluated'}
        </Typography>
        <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      </Box>
    </Tooltip>
  )
}

interface OperatorData {
  operatorType: string
  label: string
  onWinningPath: boolean
  parentTerms: string[][]
  childTerms: string[] | null
}

export function LineageOperatorNode({ data }: { data: OperatorData }) {
  const colour = operatorColor(data.operatorType)
  const Icon =
    data.operatorType === 'crossover'
      ? CallSplitRoundedIcon
      : data.operatorType === 'copy'
        ? ContentCopyRoundedIcon
        : ShuffleRoundedIcon

  return (
    <Tooltip
      title={
        <Box sx={{ whiteSpace: 'pre-line' }}>
          {data.label}
          {data.parentTerms.length > 0 &&
            `\n\nfrom:\n${data.parentTerms.map((terms) => `  ${terms.slice(0, 3).join(' · ')}`).join('\n')}`}
          {data.childTerms && `\n\nmade:\n  ${data.childTerms.slice(0, 3).join(' · ')}`}
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
          border: '1.5px solid',
          borderColor: colour,
          bgcolor: alpha(colour, 0.18),
          opacity: data.onWinningPath ? 1 : 0.5,
        }}
      >
        <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
        <Icon sx={{ fontSize: 16, color: colour }} />
        <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      </Box>
    </Tooltip>
  )
}
