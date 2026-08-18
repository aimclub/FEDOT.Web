import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'

import type { SystemEquation, SystemFactor, SystemGraph, SystemTerm } from '../api/types'

/**
 * A discovered equation, typeset.
 *
 * This is the one thing a user of an equation-discovery tool actually came to
 * see, so it is rendered from the structured terms rather than from a string —
 * derivatives become real ∂-fractions, powers become superscripts, and the
 * numbers keep a monospace column so two candidates can be compared by eye.
 *
 * No LaTeX engine is involved. The payload carries a LaTeX form as well, for
 * pasting into a paper, but pulling in a typesetter to render `∂u/∂t` would be
 * a large dependency for a small grammar: EPDE's tokens are a fixed and short
 * list, and the parse below covers all of them.
 */

/** `d^2u/dt^2`, `du/dx` — EPDE's derivative labels, after axis renaming. */
const DERIVATIVE = /^d(?:\^(\d+))?([^/]+)\/d(.+?)(?:\^(\d+))?$/

interface Parsed {
  order: number
  variable: string
  axis: string
}

function parseDerivative(label: string): Parsed | null {
  const match = DERIVATIVE.exec(label)
  if (!match) return null
  const order = Number(match[1] ?? match[4] ?? 1)
  return { order: Number.isFinite(order) ? order : 1, variable: match[2], axis: match[3] }
}

function Superscript({ children }: { children: React.ReactNode }) {
  return (
    <Box component="span" sx={{ fontSize: '0.7em', verticalAlign: 'super', lineHeight: 0 }}>
      {children}
    </Box>
  )
}

/** A stacked fraction, the way a derivative is written by hand. */
function Fraction({ top, bottom }: { top: React.ReactNode; bottom: React.ReactNode }) {
  return (
    <Box
      component="span"
      sx={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        verticalAlign: 'middle',
        mx: 0.4,
        lineHeight: 1.15,
      }}
    >
      <Box component="span" sx={{ px: 0.4 }}>
        {top}
      </Box>
      <Box
        component="span"
        sx={{ width: '100%', borderTop: '1px solid currentColor', px: 0.4 }}
      />
      <Box component="span" sx={{ px: 0.4 }}>
        {bottom}
      </Box>
    </Box>
  )
}

function FactorView({ factor }: { factor: SystemFactor }) {
  const derivative = factor.is_deriv ? parseDerivative(factor.label) : null
  const power = Number(factor.params?.power ?? 1)

  if (derivative) {
    const { order, variable, axis } = derivative
    const body = (
      <Fraction
        top={
          <>
            ∂{order > 1 && <Superscript>{order}</Superscript>}
            <em>{variable}</em>
          </>
        }
        bottom={
          <>
            ∂<em>{axis}</em>
            {order > 1 && <Superscript>{order}</Superscript>}
          </>
        }
      />
    )
    return power > 1 ? (
      <Box component="span">
        ({body})<Superscript>{power}</Superscript>
      </Box>
    ) : (
      body
    )
  }

  // A coordinate-dependent token keeps its argument: sin(1.62 x).
  const argument = factor.name.includes('(') ? factor.name.slice(factor.name.indexOf('(')) : null
  return (
    <Box component="span">
      <em>{factor.label}</em>
      {argument}
      {power > 1 && <Superscript>{power}</Superscript>}
    </Box>
  )
}

function Coefficient({ value }: { value: number }) {
  const text =
    Math.abs(value) >= 1e-3 && Math.abs(value) < 1e4
      ? Number(value.toPrecision(4)).toString()
      : value.toExponential(2)
  return (
    <Box component="span" sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.9em' }}>
      {text}
    </Box>
  )
}

function TermView({ term }: { term: SystemTerm }) {
  return (
    <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.3 }}>
      {term.factors.map((factor, index) => (
        <Box component="span" key={factor.id} sx={{ display: 'inline-flex', alignItems: 'center' }}>
          {index > 0 && (
            <Box component="span" sx={{ mx: 0.3, opacity: 0.5 }}>
              ·
            </Box>
          )}
          <FactorView factor={factor} />
        </Box>
      ))}
      {term.factors.length === 0 && <span>1</span>}
    </Box>
  )
}

interface EquationProps {
  equation: SystemEquation
  /** Highlight one term, e.g. the one hovered in the ablation table. */
  highlightTermId?: string | null
}

export function EquationLine({ equation, highlightTermId }: EquationProps) {
  const target = equation.terms.find((term) => term.is_target)
  const active = equation.terms.filter((term) => !term.is_target && term.active)
  const intercept = equation.intercept ?? 0
  const showIntercept = Math.abs(intercept) > 1e-12

  if (!equation.fitted) {
    return (
      <Typography variant="body2" color="text.disabled">
        This candidate has not been fitted yet, so it has no coefficients.
      </Typography>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        rowGap: 1,
        fontSize: '1.05rem',
      }}
    >
      {target && (
        <Box
          component="span"
          sx={{
            px: 0.5,
            borderRadius: 1,
            bgcolor: highlightTermId === target.id ? 'action.selected' : undefined,
          }}
        >
          <TermView term={target} />
        </Box>
      )}
      <Box component="span" sx={{ mx: 1 }}>
        =
      </Box>

      {active.length === 0 && !showIntercept && <span>0</span>}

      {active.map((term, index) => {
        const coefficient = term.coefficient ?? 0
        const negative = coefficient < 0
        return (
          <Box
            component="span"
            key={term.id}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              px: 0.5,
              borderRadius: 1,
              bgcolor: highlightTermId === term.id ? 'action.selected' : undefined,
            }}
          >
            {index > 0 && (
              <Box component="span" sx={{ mx: 0.6 }}>
                {negative ? '−' : '+'}
              </Box>
            )}
            {index === 0 && negative && (
              <Box component="span" sx={{ mr: 0.3 }}>
                −
              </Box>
            )}
            <Coefficient value={Math.abs(coefficient)} />
            <Box component="span" sx={{ mx: 0.4, opacity: 0.5 }}>
              ·
            </Box>
            <TermView term={term} />
          </Box>
        )
      })}

      {showIntercept && (
        <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center' }}>
          <Box component="span" sx={{ mx: 0.6 }}>
            {intercept < 0 ? '−' : '+'}
          </Box>
          <Coefficient value={Math.abs(intercept)} />
        </Box>
      )}
    </Box>
  )
}

interface Props {
  system: SystemGraph | null | undefined
  highlightTermId?: string | null
  /** Shown when there is nothing to draw yet. */
  emptyHint?: string
}

export default function EquationView({ system, highlightTermId, emptyHint }: Props) {
  if (!system || system.equations.length === 0) {
    return (
      <Typography variant="body2" color="text.disabled">
        {emptyHint ?? 'No equation to show.'}
      </Typography>
    )
  }

  return (
    <Stack spacing={1.25}>
      {system.equations.map((equation) => (
        <Stack key={equation.variable} direction="row" spacing={1.5} alignItems="center">
          {system.equations.length > 1 && (
            <Typography
              variant="caption"
              sx={{ color: 'text.disabled', minWidth: 24, fontStyle: 'italic' }}
            >
              {equation.variable}
            </Typography>
          )}
          <EquationLine equation={equation} highlightTermId={highlightTermId} />
        </Stack>
      ))}
    </Stack>
  )
}
