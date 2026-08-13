/** Mirrors the pydantic models in `fedotweb/schemas.py`. */

export type ParameterType =
  | 'continuous'
  | 'discrete'
  | 'categorical'
  | 'nested'
  | 'boolean'
  | 'free'

export type ValueType = 'number' | 'integer' | 'string' | 'boolean' | 'array' | 'object'

export interface NestedVariant {
  label: string
  fixed: Record<string, unknown>
  options: Record<string, unknown[]>
}

/** How one hyperparameter should be presented and validated. */
export interface ParameterSchema {
  name: string
  type: ParameterType
  value_type: ValueType
  /** True when FEDOT's tuner explores this parameter. */
  tunable: boolean
  distribution: string | null
  /** The sampling scope is best traversed logarithmically. */
  log_scale: boolean
  default: unknown
  minimum: number | null
  maximum: number | null
  choices: unknown[] | null
  nested_variants: NestedVariant[] | null
}

export interface OperationSummary {
  id: string
  kind: string
  group: string
  family: string | null
  description: string | null
  tags: string[]
  presets: string[]
  tasks: string[]
  input_types: string[]
  output_types: string[]
  allowed_positions: string[]
  is_default: boolean
}

export interface OperationDetail extends OperationSummary {
  parameters: ParameterSchema[]
  defaults: Record<string, unknown>
}

export interface GraphNode {
  id: string
  operation: string
  params: Record<string, unknown>
  label?: string | null
  kind?: string | null
  group?: string | null
  description?: string | null
  tags: string[]
  defaults: Record<string, unknown>
  parents: string[]
  children: string[]
  is_primary: boolean
  is_root: boolean
}

export interface GraphEdge {
  id?: string | null
  source: string
  target: string
}

export interface PipelineGraph {
  uid: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  depth: number
  length: number
}

export interface PipelineRecord {
  uid: string
  name: string
  task: string | null
  origin: string | null
  run_uid: string | null
  created_at: string
  updated_at: string
  length: number
  depth: number
  graph?: PipelineGraph | null
}

export interface ValidationResult {
  is_valid: boolean
  problems: string[]
  depth: number
  length: number
}

export interface DatasetColumn {
  name: string
  index: number
  type: string
  distinct_sample: number
  missing_sample: number
  examples: string[]
}

export interface DatasetRecord {
  uid: string
  name: string
  filename: string
  task: string | null
  target: string | null
  n_rows: number | null
  n_columns: number | null
  columns: DatasetColumn[]
  created_at: string
}

export interface DatasetUploadResult extends DatasetRecord {
  preview: Record<string, unknown>[]
  suggested_target: string | null
}

export type Problem = 'classification' | 'regression' | 'ts_forecasting'

export interface RunConfig {
  problem: Problem
  dataset_uid: string
  target?: string | null
  timeout: number
  preset: string
  metric?: string | null
  seed?: number | null
  n_jobs: number
  cv_folds: number
  pop_size: number
  num_of_generations: number
  max_depth: number
  max_arity: number
  with_tuning: boolean
  early_stopping_iterations?: number | null
  available_operations?: string[] | null
  forecast_length: number
  initial_pipeline?: PipelineGraph | null
  logging_level: number
}

export type RunStatus = 'pending' | 'running' | 'finished' | 'failed' | 'cancelled'

export interface RunRecord {
  uid: string
  name: string
  dataset_uid: string | null
  config: Record<string, unknown>
  status: RunStatus
  error: string | null
  metrics: Record<string, number> | null
  best_pipeline: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

/**
 * Knobs that can be turned while the evolution is running. `null` on a field
 * means "leave GOLEM's own policy in charge".
 */
export interface EvolutionControls {
  pop_size: number | null
  num_of_generations: number | null
  timeout_minutes: number | null
  mutation_prob: number | null
  crossover_prob: number | null
  /** Stop after the current generation, keeping the best pipeline found so far. */
  finish_now: boolean
}

/** What the optimiser is actually using right now. */
export interface EffectiveParams {
  generation: number
  pop_size: number | null
  mutation_prob: number | null
  crossover_prob: number | null
  num_of_generations: number | null
  timeout_minutes: number | null
  max_depth: number | null
}

export interface RunControlState {
  requested: EvolutionControls
  effective: EffectiveParams | null
  can_control: boolean
  applied: string[]
}

export interface GenerationPoint {
  generation: number
  size: number
  best_fitness: number | null
  mean_fitness: number | null
  worst_fitness: number | null
  elapsed?: number | null
}

export interface RunProgress {
  run: RunRecord
  generations: GenerationPoint[]
  best_pipeline: PipelineGraph | null
  last_event_id: number
}

export interface RunEvent {
  id?: number
  kind: string
  payload: Record<string, unknown>
  elapsed?: number | null
  created_at?: string
}

/** One node of the evolution genealogy: a pipeline, or the operator that made it. */
export interface LineageNode {
  id: string
  kind: 'individual' | 'operator'
  uid: string
  generation: number
  /** Individuals sit on even layers, the operators that produced them on odd ones. */
  layer: number
  on_winning_path: boolean

  // individual
  index?: number | null
  fitness?: number | null
  operations: string[]
  length?: number | null
  native_generation?: number | null
  is_best_in_generation: boolean
  is_final_choice: boolean
  /** While a run is going there is no final choice, only a leader so far. */
  is_current_best: boolean

  // operator
  operator_type?: string | null
  label?: string | null
}

export interface LineageEdge {
  id: string
  source: string
  target: string
  /** `survival`, `produces`, `chain`, or the operator type that created it. */
  kind: string
}

/**
 * One stored generation. GOLEM records the seed populations and the final choice
 * alongside the real generations, so `is_evolutionary` separates the two.
 */
export interface GenerationInfo {
  index: number
  label: string
  raw_label: string
  size: number
  is_evolutionary: boolean
}

export interface LineageGraph {
  nodes: LineageNode[]
  edges: LineageEdge[]
  /** Every stored generation, including the seed and result pseudo-generations. */
  generations: number
  /** How many of those were actual rounds of evolution. */
  evolution_generations: number
  generation_meta: GenerationInfo[]
  only_winning_path: boolean
  truncated: boolean
  metric_names: string[]
  /** `history` for a finished run, `live` when assembled from progress events. */
  source: 'history' | 'live'
  is_live: boolean
}

export interface IndividualPipeline extends PipelineGraph {
  fitness: number | null
  generation: number | null
}

export type AnalysisKind = 'objective' | 'sensitivity'

export interface AnalysisRecord {
  uid: string
  run_uid: string
  kind: AnalysisKind
  pipeline_uid: string | null
  options: Record<string, unknown>
  status: 'running' | 'finished' | 'failed'
  error: string | null
  result: ObjectiveResult | SensitivityResult | null
  created_at: string
  finished_at: string | null
}

export interface FoldResult {
  fold: number
  failed: boolean
  error?: string
  train_size?: number
  test_size?: number
  /** As FEDOT computes them: negated for metrics it maximises. */
  metrics: Record<string, number | null>
  /** The same numbers as a person reads them. */
  readable?: Record<string, number | null>
}

export interface MetricSummary {
  mean: number
  readable_mean: number
  min: number
  max: number
  spread: number
  folds_used: number
  is_maximised: boolean
}

export interface ObjectiveResult {
  kind: 'objective'
  problem: string
  primary_metric: string | null
  cv_folds: number
  metrics: string[]
  folds: FoldResult[]
  summary: Record<string, MetricSummary | null>
  holdout: {
    size: number
    metrics: Record<string, number | null>
    readable: Record<string, number | null>
    error: string | null
  }
  note: string
}

export interface SensitivityEntity {
  iteration: number
  entity_type: 'node' | 'edge'
  entity: string
  operation: string | null
  approaches: Record<string, unknown>
  worst: { entity_idx?: string; approach_name?: string; value?: number } | null
  /**
   * Whether the best change to this part improved the objective. GOLEM's ratio
   * is sign-normalised, so the backend decides this once; `null` means the
   * change could not be evaluated. Absent on results computed before this field
   * existed.
   */
  improves?: boolean | null
  /** Distance of the ratio from 1 — how much the change mattered either way. */
  severity?: number
}

export interface SensitivityResult {
  kind: 'sensitivity'
  metric: string
  is_maximised: boolean
  entities: SensitivityEntity[]
  note: string
}

export interface PreprocessingStep {
  id: string
  title: string
  detail: string
  columns: number[]
  applied: boolean
}

export interface PreprocessingReport {
  problem: string
  target: string
  rows: Record<string, number>
  columns: Record<string, number>
  source_types: Record<string, unknown>[]
  /** Type each file column reaches the pipeline as; null where it was dropped. */
  final_types: (string | null)[]
  target_type: string | null
  steps: PreprocessingStep[]
  note: string
}

export interface TaskInfo {
  id: string
  label: string
}

export interface MetricInfo {
  id: string
  label: string
  tasks: string[]
}

export interface PresetInfo {
  id: string
  label: string
  description: string
}

export interface Capabilities {
  fedot_version: string
  golem_version: string | null
  tasks: TaskInfo[]
  metrics: MetricInfo[]
  presets: PresetInfo[]
  max_run_timeout_minutes: number
  max_concurrent_runs: number
}
