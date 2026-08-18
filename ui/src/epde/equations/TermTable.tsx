import { useState } from 'react'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import LinearProgress from '@mui/material/LinearProgress'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'

import type { AblationReport, SystemEquation } from '../api/types'

/**
 * What the equation rests on, term by term.
 *
 * The FEDOT.Web counterpart deletes each node of a pipeline and refits. An
 * equation is linear in its coefficients, so the same question needs no refit:
 * the residual with a term removed is read straight off the design matrix the
 * fit already used.
 *
 * The number shown is what the equation would be left explaining without the
 * term. It is used rather than the growth factor because it is always defined —
 * an exact fit has a zero residual, and the ratio against zero is undefined
 * exactly for the best result a search can produce.
 */

const percent = (value: number | null | undefined) =>
  value === null || value === undefined ? '—' : `${(value * 100).toFixed(1)}%`

const coefficient = (value: number) =>
  Math.abs(value) >= 1e-3 && Math.abs(value) < 1e4
    ? Number(value.toPrecision(4)).toString()
    : value.toExponential(2)

interface Props {
  equation: SystemEquation
  ablation?: AblationReport | null
  onHighlight?: (termId: string | null) => void
}

export default function TermTable({ equation, ablation, onHighlight }: Props) {
  const [hovered, setHovered] = useState<string | null>(null)

  const byIndex = new Map((ablation?.terms ?? []).map((entry) => [entry.index, entry]))
  const rows = equation.terms.filter((term) => term.active || byIndex.get(term.index)?.active)

  return (
    <Stack spacing={1}>
      {ablation?.error && (
        <Alert severity="info" variant="outlined" sx={{ py: 0.25 }}>
          {ablation.error}
        </Alert>
      )}

      {ablation && !ablation.error && (
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
          <Tooltip title="Residual of the fitted equation, relative to its left-hand side. Smaller is a closer fit.">
            <Chip
              size="small"
              variant="outlined"
              label={`residual ${percent(ablation.relative_residual)}`}
            />
          </Tooltip>
          <Typography variant="caption" color="text.disabled">
            Residuals here are unweighted, so they are comparable with each other but not with the
            objective value on the Pareto chart, which EPDE weights by its test function.
          </Typography>
        </Stack>
      )}

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Term</TableCell>
            <TableCell align="right">Coefficient</TableCell>
            <TableCell align="right">
              <Tooltip title="The residual the equation would be left with if this term were removed, measured against its left-hand side. Above 100% means the leftover is larger than what the equation is trying to explain — the equation rests on the term entirely.">
                <span>Residual without it</span>
              </Tooltip>
            </TableCell>
            <TableCell align="right">
              <Tooltip title="Size of the term next to the left-hand side. Explains a large effect from a small coefficient, and a small one from a large coefficient.">
                <span>Size</span>
              </Tooltip>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((term) => {
            const entry = byIndex.get(term.index)
            const share = entry?.residual_without ?? null
            return (
              <TableRow
                key={term.id}
                hover
                onMouseEnter={() => {
                  setHovered(term.id)
                  onHighlight?.(term.id)
                }}
                onMouseLeave={() => {
                  setHovered(null)
                  onHighlight?.(null)
                }}
                selected={hovered === term.id}
              >
                <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.78rem' }}>
                  {term.name}
                  {term.is_target && (
                    <Chip size="small" label="left-hand side" sx={{ ml: 1, height: 18 }} />
                  )}
                </TableCell>
                <TableCell align="right" sx={{ fontFamily: '"JetBrains Mono", monospace' }}>
                  {term.is_target ? '—' : coefficient(term.coefficient ?? 0)}
                </TableCell>
                <TableCell align="right" sx={{ minWidth: 120 }}>
                  {share === null ? (
                    '—'
                  ) : (
                    <Stack direction="row" spacing={1} alignItems="center" justifyContent="flex-end">
                      <Box sx={{ width: 56 }}>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(100, share * 100)}
                          color={share > 0.5 ? 'primary' : 'inherit'}
                        />
                      </Box>
                      <span>{percent(share)}</span>
                    </Stack>
                  )}
                </TableCell>
                <TableCell align="right">{percent(entry?.magnitude)}</TableCell>
              </TableRow>
            )
          })}
          {rows.length === 0 && (
            <TableRow>
              <TableCell colSpan={4}>
                <Typography variant="body2" color="text.disabled">
                  Every term was driven to zero; this candidate says nothing.
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Stack>
  )
}
