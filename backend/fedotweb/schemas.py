"""Request and response models for the HTTP API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ParameterType = Literal["continuous", "discrete", "categorical", "nested", "boolean", "free"]
ValueType = Literal["number", "integer", "string", "boolean", "array", "object"]


class NestedVariant(BaseModel):
    label: str
    fixed: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, list[Any]] = Field(default_factory=dict)


class ParameterSchema(BaseModel):
    """How a single hyperparameter should be presented and validated."""

    name: str
    type: ParameterType
    value_type: ValueType
    #: ``True`` when FEDOT's tuner explores this parameter.
    tunable: bool
    #: Name of the underlying hyperopt distribution, when there is one.
    distribution: str | None = None
    #: Whether the sampling scope is best traversed logarithmically.
    log_scale: bool = False
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None
    choices: list[Any] | None = None
    nested_variants: list[NestedVariant] | None = None


class OperationSummary(BaseModel):
    id: str
    kind: str
    group: str
    family: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    presets: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    input_types: list[str] = Field(default_factory=list)
    output_types: list[str] = Field(default_factory=list)
    allowed_positions: list[str] = Field(default_factory=list)
    is_default: bool = True


class OperationDetail(OperationSummary):
    parameters: list[ParameterSchema] = Field(default_factory=list)
    defaults: dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    id: str
    operation: str
    params: dict[str, Any] = Field(default_factory=dict)

    # Fields the backend fills in when describing a pipeline; accepted but ignored
    # on the way in so the UI can post back exactly what it received.
    label: str | None = None
    kind: str | None = None
    group: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    defaults: dict[str, Any] = Field(default_factory=dict)
    parents: list[str] = Field(default_factory=list)
    children: list[str] = Field(default_factory=list)
    is_primary: bool = False
    is_root: bool = False

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value: Any) -> str:
        # The legacy frontend used integer node ids.
        return str(value)


class GraphEdge(BaseModel):
    source: str
    target: str
    id: str | None = None

    @field_validator("source", "target", mode="before")
    @classmethod
    def _coerce_endpoint(cls, value: Any) -> str:
        return str(value)


class PipelineGraph(BaseModel):
    uid: str = ""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    depth: int = 0
    length: int = 0


class PipelineRecord(BaseModel):
    uid: str
    name: str
    task: str | None = None
    origin: str | None = None
    run_uid: str | None = None
    created_at: str
    updated_at: str
    length: int = 0
    depth: int = 0
    graph: PipelineGraph | None = None


class SavePipelineRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    task: str | None = None
    graph: PipelineGraph
    uid: str | None = None


class ValidatePipelineRequest(BaseModel):
    graph: PipelineGraph
    task: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    problems: list[str] = Field(default_factory=list)
    depth: int = 0
    length: int = 0


class DatasetColumn(BaseModel):
    name: str
    index: int
    type: str
    distinct_sample: int = 0
    missing_sample: int = 0
    examples: list[str] = Field(default_factory=list)


class DatasetRecord(BaseModel):
    uid: str
    name: str
    filename: str
    task: str | None = None
    target: str | None = None
    n_rows: int | None = None
    n_columns: int | None = None
    columns: list[DatasetColumn] = Field(default_factory=list)
    created_at: str


class DatasetUploadResult(DatasetRecord):
    preview: list[dict[str, Any]] = Field(default_factory=list)
    suggested_target: str | None = None


class RunConfig(BaseModel):
    """Everything the run form can set, mapped onto FEDOT's API parameters."""

    problem: Literal["classification", "regression", "ts_forecasting"]
    dataset_uid: str
    target: str | None = None

    timeout: float = Field(default=5.0, gt=0, description="Composition budget in minutes")
    preset: str = "auto"
    metric: str | None = None
    seed: int | None = None
    n_jobs: int = Field(default=1, ge=-1)
    cv_folds: int = Field(default=5, ge=2, le=20)

    pop_size: int = Field(default=20, ge=2, le=200)
    num_of_generations: int = Field(default=20, ge=1, le=500)
    max_depth: int = Field(default=6, ge=1, le=20)
    max_arity: int = Field(default=4, ge=1, le=20)
    with_tuning: bool = True
    early_stopping_iterations: int | None = Field(default=None, ge=1)

    available_operations: list[str] | None = None
    forecast_length: int = Field(default=30, ge=1)
    initial_pipeline: PipelineGraph | None = None

    logging_level: int = 20


class StartRunRequest(BaseModel):
    name: str | None = None
    config: RunConfig


class RunRecord(BaseModel):
    uid: str
    name: str
    dataset_uid: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    status: str
    error: str | None = None
    metrics: dict[str, float] | None = None
    best_pipeline: str | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None


class EvolutionControls(BaseModel):
    """Knobs that can be turned while the evolution is running.

    `None` on a field means "leave GOLEM's own policy in charge"; setting a value
    pins it until it is cleared again.
    """

    pop_size: int | None = Field(default=None, ge=2, le=500)
    num_of_generations: int | None = Field(default=None, ge=1, le=10_000)
    timeout_minutes: float | None = Field(default=None, gt=0)
    mutation_prob: float | None = Field(default=None, ge=0.0, le=1.0)
    crossover_prob: float | None = Field(default=None, ge=0.0, le=1.0)
    #: Stop after the current generation, keeping the best pipeline found so far.
    finish_now: bool = False


class EffectiveParams(BaseModel):
    """What the optimiser is actually using right now."""

    generation: int = 0
    pop_size: int | None = None
    mutation_prob: float | None = None
    crossover_prob: float | None = None
    num_of_generations: int | None = None
    timeout_minutes: float | None = None
    max_depth: int | None = None


class RunControlState(BaseModel):
    requested: EvolutionControls = Field(default_factory=EvolutionControls)
    effective: EffectiveParams | None = None
    #: False once the run ends; the controls then have nothing to act on.
    can_control: bool = False
    #: Most recent changes the worker reported applying.
    applied: list[str] = Field(default_factory=list)


class RunEvent(BaseModel):
    id: int
    created_at: str
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class GenerationPoint(BaseModel):
    """One point on the evolution chart."""

    generation: int
    size: int
    best_fitness: float | None = None
    mean_fitness: float | None = None
    worst_fitness: float | None = None
    elapsed: float | None = None
    #: Identity of the generation's best individual, so the chart can mark the
    #: generations where the leader actually changed.
    best_uid: str | None = None
    best_operations: list[str] = Field(default_factory=list)


class RunProgress(BaseModel):
    run: RunRecord
    generations: list[GenerationPoint] = Field(default_factory=list)
    best_pipeline: PipelineGraph | None = None
    last_event_id: int = 0


class LineageNode(BaseModel):
    """One node of the evolution genealogy.

    Individuals and operators share the payload; `kind` says which fields apply.
    """

    id: str
    kind: Literal["individual", "operator"]
    uid: str
    generation: int
    #: Individuals sit on even layers, the operators that produced them on odd ones.
    layer: int
    on_winning_path: bool = False

    # individual
    index: int | None = None
    fitness: float | None = None
    operations: list[str] = Field(default_factory=list)
    length: int | None = None
    native_generation: int | None = None
    is_best_in_generation: bool = False
    is_final_choice: bool = False
    #: While a run is going there is no final choice, only a leader so far.
    is_current_best: bool = False

    # operator
    operator_type: str | None = None
    label: str | None = None


class LineageEdge(BaseModel):
    id: str
    source: str
    target: str
    #: `survival`, `produces`, `chain`, or the operator type that created it.
    kind: str


class GenerationInfo(BaseModel):
    """One stored generation, which may be evolution or bookkeeping.

    GOLEM records the seed populations and the final choice alongside the real
    generations, so `is_evolutionary` separates the two.
    """

    index: int
    label: str
    raw_label: str = ""
    size: int = 0
    is_evolutionary: bool = True


class LineageGraph(BaseModel):
    nodes: list[LineageNode] = Field(default_factory=list)
    edges: list[LineageEdge] = Field(default_factory=list)
    #: Every stored generation, including the seed and result pseudo-generations.
    generations: int = 0
    #: How many of those were actual rounds of evolution.
    evolution_generations: int = 0
    generation_meta: list[GenerationInfo] = Field(default_factory=list)
    #: True when only the ancestry of the final choice is included.
    only_winning_path: bool = True
    #: In the winning-path view, how many trailing generations were dropped
    #: because the best fitness never improved in them.
    hidden_plateau_generations: int = 0
    #: True when the individual cap was hit and the graph is incomplete.
    truncated: bool = False
    metric_names: list[str] = Field(default_factory=list)
    #: `history` for a finished run, `live` when assembled from progress events.
    source: Literal["history", "live"] = "history"
    is_live: bool = False


class IndividualPipeline(PipelineGraph):
    """The pipeline behind one node of the genealogy."""

    fitness: float | None = None
    generation: int | None = None


class StartAnalysisRequest(BaseModel):
    """Ask for an on-demand analysis of one pipeline from a run."""

    kind: Literal["objective", "sensitivity"]
    #: Which pipeline to analyse. Defaults to the run's best.
    pipeline_uid: str | None = None
    #: Or an individual from the run's genealogy.
    individual_uid: str | None = None
    #: Sensitivity only: how many replacement operations to try per node.
    replacements: int = Field(default=2, ge=1, le=10)
    analyse_edges: bool = True


class StandaloneAnalysisRequest(BaseModel):
    """Ask for an analysis of a pipeline that is not tied to a run.

    The editor uses this: the pipeline is fitted on the chosen dataset first,
    so the analysis pays for those fits with no run to borrow them from.
    """

    kind: Literal["objective", "sensitivity"]
    graph: PipelineGraph
    dataset_uid: str
    #: Defaults to the dataset's own target column.
    target: str | None = None
    #: Defaults to the dataset's task.
    problem: str | None = None
    metric: str | None = None
    cv_folds: int = Field(default=5, ge=2, le=10)
    seed: int | None = None
    #: Sensitivity only: how many replacement operations to try per node.
    replacements: int = Field(default=2, ge=1, le=10)
    analyse_edges: bool = True


class AnalysisRecord(BaseModel):
    uid: str
    run_uid: str
    kind: str
    pipeline_uid: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    status: str
    error: str | None = None
    #: Shape depends on `kind`; see the analysis worker.
    result: dict[str, Any] | None = None
    created_at: str
    finished_at: str | None = None


class PreprocessingStep(BaseModel):
    id: str
    title: str
    detail: str
    columns: list[int] = Field(default_factory=list)
    applied: bool = False


class PreprocessingReport(BaseModel):
    """What FEDOT's obligatory preprocessing does to a dataset."""

    problem: str
    target: str
    rows: dict[str, int] = Field(default_factory=dict)
    columns: dict[str, int] = Field(default_factory=dict)
    #: Per-column counts of the types actually found in the raw file, in file order.
    source_types: list[dict[str, Any]] = Field(default_factory=list)
    #: Type each file column reaches the pipeline as; None where it was dropped.
    final_types: list[str | None] = Field(default_factory=list)
    target_type: str | None = None
    steps: list[PreprocessingStep] = Field(default_factory=list)
    note: str = ""


class TaskInfo(BaseModel):
    id: str
    label: str


class MetricInfo(BaseModel):
    id: str
    label: str
    tasks: list[str] = Field(default_factory=list)


class PresetInfo(BaseModel):
    id: str
    label: str
    description: str


class CapabilitiesResponse(BaseModel):
    """Everything the run-configuration form needs in one request."""

    fedot_version: str
    golem_version: str | None = None
    tasks: list[TaskInfo] = Field(default_factory=list)
    metrics: list[MetricInfo] = Field(default_factory=list)
    presets: list[PresetInfo] = Field(default_factory=list)
    max_run_timeout_minutes: float = 240.0
    max_concurrent_runs: int = 2
