import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { alpha, useTheme } from '@mui/material/styles'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import FlagRoundedIcon from '@mui/icons-material/FlagRounded'
import InputRoundedIcon from '@mui/icons-material/InputRounded'
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded'

import { groupColor } from '../theme'
import { formatParamValue } from './paramDisplay'

export interface PipelineNodeData extends Record<string, unknown> {
  operation: string
  group: string
  kind: string
  description?: string | null
  tags: string[]
  /** Parameters explicitly set on this node. */
  params: Record<string, unknown>
  /** Defaults FEDOT would apply, used to mark what the user changed. */
  defaults: Record<string, unknown>
  isPrimary: boolean
  isRoot: boolean
  /** Rows displayed on the card; precomputed so layout can size the node. */
  visibleParams: { name: string; value: unknown; changed: boolean }[]
  paramCount: number
  hiddenParamCount: number
  problem?: string | null
  readOnly?: boolean
  /** Must match the layout direction so the handles line up with the edges. */
  horizontal: boolean
}

export type PipelineFlowNode = Node<PipelineNodeData, 'pipelineNode'>

/**
 * A pipeline node drawn as a card.
 *
 * The old editor rendered a circle with the text `name id:0` and kept
 * hyperparameters entirely out of sight. Here the operation, its category and
 * the parameters that actually differ from FEDOT's defaults are all legible at
 * a glance, which is what makes a composed pipeline reviewable without clicking
 * through every node.
 */
export default function PipelineNodeCard({ data, selected }: NodeProps<PipelineFlowNode>) {
  const theme = useTheme()
  const accent = groupColor(data.group)
  const hasProblem = Boolean(data.problem)

  return (
    <Box
      sx={{
        // The size is declared on the flow node so React Flow can route edges
        // without measuring; the card simply fills it.
        width: '100%',
        height: '100%',
        borderRadius: 2,
        overflow: 'hidden',
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: hasProblem
          ? theme.palette.error.main
          : selected
            ? accent
            : theme.palette.divider,
        boxShadow: selected
          ? `0 0 0 2px ${alpha(accent, 0.45)}, 0 8px 24px ${alpha('#000', 0.18)}`
          : `0 1px 3px ${alpha('#000', 0.16)}`,
        transition: 'box-shadow 120ms ease, border-color 120ms ease',
      }}
    >
      <Handle
        type="target"
        position={data.horizontal ? Position.Left : Position.Top}
        style={{
          width: 9,
          height: 9,
          background: accent,
          border: 'none',
          // Primary nodes take no input, so the dot is hidden — but the handle
          // itself stays mounted so its geometry matches what layout declared.
          opacity: data.isPrimary ? 0 : 1,
        }}
        isConnectable={!data.readOnly}
      />

      <Box sx={{ height: 3, bgcolor: accent }} />

      <Box sx={{ px: 1.25, pt: 0.85, pb: 1 }}>
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Tooltip title={data.description ?? data.operation} placement="top">
            <Typography
              variant="subtitle2"
              noWrap
              sx={{ flexGrow: 1, fontFamily: '"JetBrains Mono", monospace', fontSize: '0.86rem' }}
            >
              {data.operation}
            </Typography>
          </Tooltip>

          {data.isPrimary && (
            <Tooltip title="Primary node — receives the input data">
              <InputRoundedIcon sx={{ fontSize: 15, color: 'text.disabled' }} />
            </Tooltip>
          )}
          {data.isRoot && (
            <Tooltip title="Root node — produces the prediction">
              <FlagRoundedIcon sx={{ fontSize: 15, color: accent }} />
            </Tooltip>
          )}
          {hasProblem && (
            <Tooltip title={data.problem ?? ''}>
              <WarningAmberRoundedIcon sx={{ fontSize: 16, color: 'error.main' }} />
            </Tooltip>
          )}
        </Stack>

        <Chip
          label={data.group.replace(/_/g, ' ')}
          size="small"
          sx={{
            mt: 0.4,
            height: 17,
            fontSize: '0.62rem',
            bgcolor: alpha(accent, 0.14),
            color: accent,
            '& .MuiChip-label': { px: 0.7 },
          }}
        />

        {data.visibleParams.length > 0 && (
          <Stack sx={{ mt: 0.7, gap: 0.15 }}>
            {data.visibleParams.map((param) => (
              <Stack key={param.name} direction="row" spacing={0.5} sx={{ minWidth: 0 }}>
                <Typography
                  noWrap
                  sx={{
                    fontSize: '0.68rem',
                    color: 'text.secondary',
                    fontFamily: '"JetBrains Mono", monospace',
                    maxWidth: 96,
                  }}
                >
                  {param.name}
                </Typography>
                <Typography
                  noWrap
                  sx={{
                    fontSize: '0.68rem',
                    flexGrow: 1,
                    textAlign: 'right',
                    fontFamily: '"JetBrains Mono", monospace',
                    fontWeight: param.changed ? 700 : 400,
                    color: param.changed ? accent : 'text.primary',
                  }}
                >
                  {formatParamValue(param.value)}
                </Typography>
              </Stack>
            ))}
            {data.hiddenParamCount > 0 && (
              <Typography sx={{ fontSize: '0.64rem', color: 'text.disabled' }}>
                +{data.hiddenParamCount} more
              </Typography>
            )}
          </Stack>
        )}

        {data.visibleParams.length === 0 && (
          <Typography sx={{ mt: 0.6, fontSize: '0.68rem', color: 'text.disabled' }}>
            default hyperparameters
          </Typography>
        )}
      </Box>

      <Handle
        type="source"
        position={data.horizontal ? Position.Right : Position.Bottom}
        style={{ width: 9, height: 9, background: accent, border: 'none' }}
        isConnectable={!data.readOnly}
      />
    </Box>
  )
}
