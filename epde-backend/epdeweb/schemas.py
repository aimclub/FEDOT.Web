"""Request and response models.

Kept in one module, like the FEDOT.Web backend, so the TypeScript mirror in
``ui/src/epde/api/types.ts`` has a single file to track.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

RunStatus = Literal["pending", "running", "finished", "failed", "cancelled"]


# ------------------------------------------------------------------ capability


class TokenFamilyParam(BaseModel):
    name: str
    type: str
    label: str
    default: Any = None


class TokenFamilyInfo(BaseModel):
    id: str
    label: str
    description: str
    params: list[TokenFamilyParam] = Field(default_factory=list)
    #: False when the installed EPDE has no such family.
    available: bool = True


class ControlInfo(BaseModel):
    name: str
    label: str
    description: str
    minimum: float
    maximum: float
    operators: list[str] = Field(default_factory=list)
    parameter: str


class SampleInfo(BaseModel):
    id: str
    name: str
    description: str
    #: The equation the search should recover, so a run can be judged.
    expected: str
    expected_latex: str
    variables: list[str]
    suggestion: dict[str, Any] = Field(default_factory=dict)


class Capabilities(BaseModel):
    """What this server can do, and what the installed EPDE supports."""

    module_version: str
    epde_available: bool
    epde_version: str | None = None
    epde_error: str | None = None
    features: dict[str, bool] = Field(default_factory=dict)
    preprocessors: list[str] = Field(default_factory=list)
    token_families: list[TokenFamilyInfo] = Field(default_factory=list)
    controls: list[ControlInfo] = Field(default_factory=list)
    samples: list[SampleInfo] = Field(default_factory=list)
    max_run_timeout_minutes: float
    max_concurrent_runs: int
    max_grid_nodes: int


# -------------------------------------------------------------------- datasets


class AxisInfo(BaseModel):
    name: str
    size: int
    start: float
    stop: float
    step: float | None = None
    #: EPDE's derivative preprocessors assume an even grid.
    uniform: bool = True


class VariableInfo(BaseModel):
    name: str
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    missing: int = 0


class DatasetRecord(BaseModel):
    uid: str
    name: str
    filename: str
    kind: str
    variables: list[VariableInfo] = Field(default_factory=list)
    axes: list[AxisInfo] = Field(default_factory=list)
    shape: list[int] = Field(default_factory=list)
    origin: str | None = None
    note: str | None = None
    created_at: str
    #: Problems found while reading the upload, e.g. missing coordinates.
    warnings: list[str] = Field(default_factory=list)


class AxisPatch(BaseModel):
    name: str | None = None
    start: float | None = None
    stop: float | None = None


class UpdateAxesRequest(BaseModel):
    axes: list[AxisPatch]


class PreviewSeries(BaseModel):
    name: str
    values: list[float | None]


class PreviewSurface(BaseModel):
    name: str
    values: list[list[float | None]]
    min: float
    max: float


class DatasetPreview(BaseModel):
    kind: Literal["series", "field"]
    axes: list[AxisInfo] = Field(default_factory=list)
    x: list[float] | None = None
    series: list[PreviewSeries] | None = None
    rows: list[float] | None = None
    columns: list[float] | None = None
    fixed: dict[str, int] = Field(default_factory=dict)
    surfaces: list[PreviewSurface] | None = None


# ------------------------------------------------------------------- equations


class SystemFactor(BaseModel):
    id: str
    #: The token label with the dataset's axis names substituted in.
    label: str
    #: What EPDE itself calls it, with positional axes (``du/dx0``).
    epde_label: str = ""
    name: str
    latex: str
    family: str
    variable: str
    is_deriv: bool
    deriv_code: list[int] | None = None
    params: dict[str, float] = Field(default_factory=dict)


class SystemTerm(BaseModel):
    id: str
    index: int
    name: str
    full_name: str
    latex: str
    coefficient: float | None = None
    is_target: bool
    #: False for a term the sparse regression drove to zero.
    active: bool
    factors: list[SystemFactor] = Field(default_factory=list)


class SystemEquation(BaseModel):
    variable: str
    terms: list[SystemTerm] = Field(default_factory=list)
    target_term: str | None = None
    intercept: float | None = None
    fitted: bool = False
    text: str
    latex: str
    epde_text: str | None = None
    metaparameters: dict[str, Any] = Field(default_factory=dict)
    discrepancy: float | None = None


class SystemNode(BaseModel):
    id: str
    kind: Literal["system", "equation", "term", "factor"]
    label: str
    latex: str = ""
    variable: str | None = None
    coefficient: float | None = None
    active: bool = True
    is_target: bool = False
    params: dict[str, Any] = Field(default_factory=dict)
    family: str | None = None
    is_deriv: bool | None = None


class SystemEdge(BaseModel):
    source: str
    target: str


class SystemGraph(BaseModel):
    """A candidate system of equations, as the browser draws it."""

    uid: str = ""
    generation: int | None = None
    variables: list[str] = Field(default_factory=list)
    equations: list[SystemEquation] = Field(default_factory=list)
    nodes: list[SystemNode] = Field(default_factory=list)
    edges: list[SystemEdge] = Field(default_factory=list)
    objectives: list[float] | None = None
    objective_names: list[str] | None = None
    active_terms: int = 0
    complexity: int = 0
    text: str = ""
    latex: str = ""


class SystemRecord(BaseModel):
    uid: str
    name: str
    run_uid: str | None = None
    origin: str | None = None
    graph: SystemGraph
    created_at: str
    updated_at: str


# ------------------------------------------------------------------------ runs


class TokenFamilyRequest(BaseModel):
    id: str
    params: dict[str, Any] = Field(default_factory=dict)


class RunConfig(BaseModel):
    dataset_uid: str
    #: Which of the dataset's variables the system should describe. All of them
    #: by default, which is what discovering a system of equations means.
    variables: list[str] | None = None

    multiobjective: bool = True
    population_size: int = Field(default=8, ge=2, le=200)
    epochs: int = Field(default=15, ge=1, le=1000)
    #: Wall-clock ceiling in minutes. EPDE has no budget of its own; this is
    #: enforced at generation boundaries so the run still returns a population.
    timeout: float | None = Field(default=None, gt=0)

    max_deriv_order: int | list[int] = 2
    equation_terms_max_number: int = Field(default=5, ge=2, le=30)
    equation_factors_max_number: int | dict[str, Any] = 1
    sparsity_min: float = Field(default=1e-8, gt=0)
    sparsity_max: float = Field(default=1.0, gt=0)
    data_fun_pow: int = Field(default=1, ge=1, le=6)
    deriv_fun_pow: int | None = None

    boundary: int | list[int] = 0
    time_axis: int = 0
    preprocessor: str = "poly"
    preprocessor_kwargs: dict[str, Any] = Field(default_factory=dict)
    token_families: list[TokenFamilyRequest] = Field(default_factory=list)

    #: EPDE master can put coefficient stability on the second Pareto axis in
    #: place of complexity. ``None`` leaves the build's own default.
    use_pic: bool | None = None
    device: str = "cpu"
    memory_for_cache: int = Field(default=15, ge=1, le=90)
    seed: int | None = None


class StartRunRequest(BaseModel):
    name: str | None = None
    config: RunConfig


class RunRecord(BaseModel):
    uid: str
    name: str
    dataset_uid: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    status: RunStatus
    error: str | None = None
    objectives: dict[str, Any] | None = None
    best_system: str | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None


class ObjectiveSummary(BaseModel):
    index: int
    name: str
    best: float
    worst: float
    mean: float


class GenerationPoint(BaseModel):
    generation: int
    label: str = ""
    size: int = 0
    evaluated: int = 0
    front_size: int = 0
    objectives: list[ObjectiveSummary] = Field(default_factory=list)
    #: Volume dominated by the front against a reference fixed at the first
    #: generation, so it is comparable across the run.
    hypervolume: float | None = None
    elapsed: float | None = None


class ParetoPoint(BaseModel):
    uid: str
    objectives: list[float]
    text: str = ""
    latex: str = ""
    complexity: int = 0
    active_terms: int = 0


class RunProgress(BaseModel):
    run: RunRecord
    generations: list[GenerationPoint] = Field(default_factory=list)
    objective_names: list[str] = Field(default_factory=list)
    front: list[ParetoPoint] = Field(default_factory=list)
    best_system: SystemGraph | None = None
    last_event_id: int = 0


class RunEvent(BaseModel):
    id: int | None = None
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    elapsed: float | None = None
    created_at: str | None = None


class EvolutionControls(BaseModel):
    """Knobs that can be turned while the search runs.

    ``None`` on a field means EPDE's own value is left in place.
    """

    mutation_prob: float | None = None
    equation_mutation_rate: float | None = None
    term_addition_prob: float | None = None
    crossover_prob: float | None = None
    parents_fraction: float | None = None
    term_param_mutation_rate: float | None = None
    #: Lower the generation limit; the run then ends through its normal path.
    epochs: int | None = None
    finish_now: bool = False


class RunControlState(BaseModel):
    requested: EvolutionControls
    #: What the live operators are actually using, read back from them.
    effective: dict[str, float | None] = Field(default_factory=dict)
    can_control: bool = False
    applied: list[str] = Field(default_factory=list)
    #: Operators this EPDE build actually exposed, so the GUI can grey out the
    #: controls that would land nowhere.
    available_operators: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------- lineage


class LineageNode(BaseModel):
    id: str
    kind: Literal["individual", "operator"]
    uid: str
    generation: int
    layer: int
    on_winning_path: bool = False

    # individual
    index: int | None = None
    objectives: list[float] | None = None
    pareto_rank: int | None = None
    terms: list[str] = Field(default_factory=list)
    length: int | None = None
    born_generation: int | None = None
    is_on_front: bool = False
    is_final_choice: bool = False
    is_current_best: bool = False

    # operator
    operator_type: str | None = None
    label: str | None = None


class LineageEdge(BaseModel):
    id: str
    source: str
    target: str
    #: ``survival``, ``produces``, ``chain``, or the operator type.
    kind: str


class GenerationInfo(BaseModel):
    index: int
    label: str
    raw_label: str
    size: int
    front_size: int = 0
    is_evolutionary: bool


class LineageGraph(BaseModel):
    nodes: list[LineageNode] = Field(default_factory=list)
    edges: list[LineageEdge] = Field(default_factory=list)
    generations: int = 0
    evolution_generations: int = 0
    generation_meta: list[GenerationInfo] = Field(default_factory=list)
    only_winning_path: bool = True
    hidden_plateau_generations: int = 0
    truncated: bool = False
    objective_names: list[str] = Field(default_factory=list)
    #: ``history`` for a finished run, ``live`` while it is still going.
    source: Literal["history", "live"] = "live"
    is_live: bool = True


# ------------------------------------------------------------------- ablation


class AblationTerm(BaseModel):
    term_id: str
    index: int
    name: str
    coefficient: float
    active: bool
    #: What the equation would be left explaining without this term, relative
    #: to the left-hand side. Always defined, including for an exact fit.
    residual_without: float | None = None
    #: Factor by which the residual grows when the term is removed. 1.0 means
    #: the term contributes nothing; ``None`` when the fit is already exact.
    residual_ratio: float | None = None
    magnitude: float | None = None


class AblationReport(BaseModel):
    variable: str
    #: Why the numbers are missing, when they are. An empty panel with no reason
    #: cannot be told apart from an equation that rests on nothing.
    error: str | None = None
    target_term: str
    target_name: str
    residual_rms: float
    target_rms: float
    relative_residual: float | None = None
    intercept: float
    terms: list[AblationTerm] = Field(default_factory=list)


class RunResult(BaseModel):
    generations: int = 0
    objective_names: list[str] = Field(default_factory=list)
    finished_early: str | None = None
    front: list[dict[str, Any]] = Field(default_factory=list)
    best_system: SystemGraph | None = None
    warnings: list[str] = Field(default_factory=list)
