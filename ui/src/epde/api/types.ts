/**
 * Mirrors the pydantic models in `epde-backend/epdeweb/schemas.py`.
 *
 * The EPDE mode keeps its own types rather than extending the FEDOT ones: an
 * EPDE candidate is a system of equations, not a pipeline, and it is judged by
 * a vector of objectives rather than by one fitness. Sharing a type would mean
 * every field being optional on one side or the other.
 */

export interface TokenFamilyParam {
  name: string
  type: string
  label: string
  default: unknown
}

export interface TokenFamilyInfo {
  id: string
  label: string
  description: string
  params: TokenFamilyParam[]
  /** False when the installed EPDE has no such family. */
  available: boolean
}

export interface ControlInfo {
  name: string
  label: string
  description: string
  minimum: number
  maximum: number
  operators: string[]
  parameter: string
}

export interface SampleInfo {
  id: string
  name: string
  description: string
  /** The equation the search should recover, so a run can be judged. */
  expected: string
  expected_latex: string
  variables: string[]
  suggestion: Record<string, unknown>
}

export interface EpdeCapabilities {
  module_version: string
  epde_available: boolean
  epde_version: string | null
  epde_error: string | null
  features: Record<string, boolean>
  preprocessors: string[]
  token_families: TokenFamilyInfo[]
  controls: ControlInfo[]
  samples: SampleInfo[]
  max_run_timeout_minutes: number
  max_concurrent_runs: number
  max_grid_nodes: number
}

export interface AxisInfo {
  name: string
  size: number
  start: number
  stop: number
  step: number | null
  /** EPDE's derivative preprocessors assume an even grid. */
  uniform: boolean
}

export interface VariableInfo {
  name: string
  min: number | null
  max: number | null
  mean: number | null
  missing: number
}

export interface DatasetRecord {
  uid: string
  name: string
  filename: string
  kind: 'field' | 'series' | string
  variables: VariableInfo[]
  axes: AxisInfo[]
  shape: number[]
  origin: string | null
  note: string | null
  created_at: string
  warnings: string[]
}

export interface DatasetPreview {
  kind: 'series' | 'field'
  axes: AxisInfo[]
  x?: number[] | null
  series?: { name: string; values: (number | null)[] }[] | null
  rows?: number[] | null
  columns?: number[] | null
  fixed: Record<string, number>
  surfaces?: { name: string; values: (number | null)[][]; min: number; max: number }[] | null
}

export interface SystemFactor {
  id: string
  /** The token label with the dataset's axis names substituted in. */
  label: string
  /** What EPDE itself calls it, with positional axes (`du/dx0`). */
  epde_label: string
  name: string
  latex: string
  family: string
  variable: string
  is_deriv: boolean
  deriv_code: number[] | null
  params: Record<string, number>
}

export interface SystemTerm {
  id: string
  index: number
  name: string
  full_name: string
  latex: string
  coefficient: number | null
  is_target: boolean
  /** False for a term the sparse regression drove to zero. */
  active: boolean
  factors: SystemFactor[]
}

export interface SystemEquation {
  variable: string
  terms: SystemTerm[]
  target_term: string | null
  intercept: number | null
  fitted: boolean
  text: string
  latex: string
  epde_text: string | null
  metaparameters: Record<string, unknown>
  discrepancy: number | null
}

export interface SystemNode {
  id: string
  kind: 'system' | 'equation' | 'term' | 'factor'
  label: string
  latex: string
  variable: string | null
  coefficient: number | null
  active: boolean
  is_target: boolean
  params: Record<string, unknown>
  family?: string | null
  is_deriv?: boolean | null
}

export interface SystemEdge {
  source: string
  target: string
}

export interface SystemGraph {
  uid: string
  generation: number | null
  variables: string[]
  equations: SystemEquation[]
  nodes: SystemNode[]
  edges: SystemEdge[]
  objectives: number[] | null
  objective_names: string[] | null
  active_terms: number
  complexity: number
  text: string
  latex: string
}

export interface SystemRecord {
  uid: string
  name: string
  run_uid: string | null
  origin: string | null
  graph: SystemGraph
  created_at: string
  updated_at: string
}

export interface TokenFamilyRequest {
  id: string
  params: Record<string, unknown>
}

export interface EpdeRunConfig {
  dataset_uid: string
  variables?: string[] | null
  multiobjective: boolean
  population_size: number
  epochs: number
  timeout?: number | null
  max_deriv_order: number | number[]
  equation_terms_max_number: number
  equation_factors_max_number: number | Record<string, unknown>
  sparsity_min: number
  sparsity_max: number
  data_fun_pow: number
  deriv_fun_pow?: number | null
  boundary: number | number[]
  time_axis: number
  preprocessor: string
  preprocessor_kwargs: Record<string, unknown>
  token_families: TokenFamilyRequest[]
  use_pic?: boolean | null
  device: string
  memory_for_cache: number
  seed?: number | null
}

export type RunStatus = 'pending' | 'running' | 'finished' | 'failed' | 'cancelled'

export interface EpdeRunRecord {
  uid: string
  name: string
  dataset_uid: string | null
  config: Record<string, unknown>
  status: RunStatus
  error: string | null
  objectives: Record<string, unknown> | null
  best_system: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface ObjectiveSummary {
  index: number
  name: string
  best: number
  worst: number
  mean: number
}

export interface GenerationPoint {
  generation: number
  label: string
  size: number
  evaluated: number
  front_size: number
  objectives: ObjectiveSummary[]
  /** Volume dominated by the front, against a reference fixed at generation 0. */
  hypervolume: number | null
  elapsed: number | null
}

export interface ParetoPoint {
  uid: string
  objectives: number[]
  text: string
  latex: string
  complexity: number
  active_terms: number
}

export interface RunProgress {
  run: EpdeRunRecord
  generations: GenerationPoint[]
  objective_names: string[]
  front: ParetoPoint[]
  best_system: SystemGraph | null
  last_event_id: number
}

export interface RunEvent {
  id?: number
  kind: string
  payload: Record<string, unknown>
  elapsed?: number | null
  created_at?: string
}

export interface EvolutionControls {
  mutation_prob: number | null
  equation_mutation_rate: number | null
  term_addition_prob: number | null
  crossover_prob: number | null
  parents_fraction: number | null
  term_param_mutation_rate: number | null
  /** Lower the generation limit; the run then ends through its normal path. */
  epochs: number | null
  finish_now: boolean
}

export interface RunControlState {
  requested: EvolutionControls
  effective: Record<string, number | null>
  can_control: boolean
  applied: string[]
  /** Operators this EPDE build exposed; the rest are greyed out. */
  available_operators: string[]
}

export interface LineageNode {
  id: string
  kind: 'individual' | 'operator'
  uid: string
  generation: number
  /** Candidates sit on even layers, the operators that produced them on odd ones. */
  layer: number
  on_winning_path: boolean

  // individual
  index?: number | null
  objectives?: number[] | null
  pareto_rank?: number | null
  terms: string[]
  length?: number | null
  born_generation?: number | null
  /** The multi-objective replacement for "best of this generation". */
  is_on_front: boolean
  is_final_choice: boolean
  is_current_best: boolean

  // operator
  operator_type?: string | null
  label?: string | null
}

export interface LineageEdge {
  id: string
  source: string
  target: string
  /** `survival`, `produces`, `chain`, or the operator type. */
  kind: string
}

export interface GenerationInfo {
  index: number
  label: string
  raw_label: string
  size: number
  front_size: number
  is_evolutionary: boolean
}

export interface LineageGraph {
  nodes: LineageNode[]
  edges: LineageEdge[]
  generations: number
  evolution_generations: number
  generation_meta: GenerationInfo[]
  only_winning_path: boolean
  hidden_plateau_generations: number
  truncated: boolean
  objective_names: string[]
  source: 'history' | 'live'
  is_live: boolean
}

export interface AblationTerm {
  term_id: string
  index: number
  name: string
  coefficient: number
  active: boolean
  /** What the equation would explain without this term, relative to its target. */
  residual_without: number | null
  /** Factor by which the residual grows; null when the fit is already exact. */
  residual_ratio: number | null
  magnitude: number | null
}

export interface AblationReport {
  variable: string
  /** Why the numbers are missing, when they are. */
  error: string | null
  target_term: string
  target_name: string
  residual_rms: number
  target_rms: number
  relative_residual: number | null
  intercept: number
  terms: AblationTerm[]
}

export interface FrontEntry {
  uid: string
  objectives: number[]
  text: string
  latex: string
  complexity: number
  active_terms: number
  ablation: AblationReport[]
}

export interface RunResult {
  generations: number
  objective_names: string[]
  finished_early: string | null
  front: FrontEntry[]
  best_system: SystemGraph | null
  warnings: string[]
}
