import type { GraphNode, ParameterSchema } from '../api/types'
import { MAX_VISIBLE_PARAMS } from './layout'

/** Compact rendering of a hyperparameter value for the node card. */
export function formatParamValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return String(value)
    // Keep very small and very large magnitudes readable.
    const magnitude = Math.abs(value)
    if (magnitude !== 0 && (magnitude < 1e-3 || magnitude >= 1e5)) return value.toExponential(2)
    return String(Number(value.toFixed(4)))
  }
  if (Array.isArray(value)) return `[${value.length}]`
  if (typeof value === 'object') return '{…}'
  const text = String(value)
  return text.length > 18 ? `${text.slice(0, 17)}…` : text
}

const sameValue = (a: unknown, b: unknown): boolean => {
  if (a === b) return true
  if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) < 1e-12
  if (a === null || b === null || a === undefined || b === undefined) return false
  if (typeof a === 'object' && typeof b === 'object') {
    return JSON.stringify(a) === JSON.stringify(b)
  }
  return String(a) === String(b)
}

/** True when the node overrides FEDOT's default for this parameter. */
export const isChanged = (name: string, value: unknown, defaults: Record<string, unknown>): boolean =>
  !(name in defaults) || !sameValue(value, defaults[name])

export interface VisibleParam {
  name: string
  value: unknown
  changed: boolean
}

/**
 * Choose which hyperparameters to show on a node card.
 *
 * Values the user (or evolution) changed away from the default come first —
 * those are what make one node differ from another in a composed pipeline.
 * A node with nothing set still runs with FEDOT's defaults (from
 * `default_operation_params.json`), so those are shown rather than a bare
 * "default hyperparameters" label that says nothing.
 */
export function selectVisibleParams(node: Pick<GraphNode, 'params' | 'defaults'>): {
  visible: VisibleParam[]
  hidden: number
  total: number
  /** True when the rows shown are FEDOT's defaults, not values set on the node. */
  fromDefaults: boolean
} {
  const defaults = node.defaults ?? {}
  const params = node.params ?? {}
  const hasOwn = Object.keys(params).length > 0
  const source = hasOwn ? params : defaults

  const annotated: VisibleParam[] = Object.entries(source).map(([name, value]) => ({
    name,
    value,
    changed: hasOwn ? isChanged(name, value, defaults) : false,
  }))

  annotated.sort((a, b) => {
    if (a.changed !== b.changed) return a.changed ? -1 : 1
    return a.name.localeCompare(b.name)
  })

  return {
    visible: annotated.slice(0, MAX_VISIBLE_PARAMS),
    hidden: Math.max(0, annotated.length - MAX_VISIBLE_PARAMS),
    total: annotated.length,
    fromDefaults: !hasOwn && annotated.length > 0,
  }
}

/**
 * The value in force for a parameter: what the node sets, or the schema default.
 */
export function effectiveValue(
  schema: ParameterSchema,
  params: Record<string, unknown>,
): unknown {
  return schema.name in params ? params[schema.name] : schema.default
}

/** Human-readable summary of where a tunable parameter may range. */
export function describeScope(schema: ParameterSchema): string | null {
  if (schema.type === 'categorical' && schema.choices) {
    return `one of ${schema.choices.length}`
  }
  if (schema.minimum !== null && schema.maximum !== null) {
    const scale = schema.log_scale ? ', log scale' : ''
    return `${formatParamValue(schema.minimum)} … ${formatParamValue(schema.maximum)}${scale}`
  }
  return null
}
