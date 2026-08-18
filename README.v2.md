# FEDOT.Web 2.0

Web interface for the [FEDOT](https://github.com/aimclub/FEDOT) AutoML framework and the
[GOLEM](https://github.com/aimclub/GOLEM) graph optimiser.

Version 2 is a new backend and frontend living alongside the original code
(`app/` and `frontend/`, which are untouched). It targets **FEDOT master (0.7.5) /
GOLEM 0.4.2**, starts without any external database, and can drive the framework rather
than only display pre-baked results.

```
backend/      FastAPI service (fedotweb package)
epde-backend/ optional equation-discovery module (epdeweb package)
ui/           Vite + React 19 + TypeScript frontend
app/          legacy Flask backend  (unchanged)
frontend/     legacy CRA frontend   (unchanged)
```

## Quick start

```bash
python -m venv .venv && .venv/Scripts/activate
pip install git+https://github.com/aimclub/FEDOT.git@master
pip install -e backend[dev]
cd ui && npm install && npm run build && cd ..
python -m fedotweb
```

FEDOT comes from master rather than PyPI — see [below](#why-fedot-is-installed-from-master).

Then open <http://127.0.0.1:8000>. The API reference is at `/docs`.

For frontend development, run the API and the Vite dev server side by side —
requests to `/api` are proxied, so the WebSocket works without extra configuration:

```bash
python -m fedotweb
```

```bash
cd ui && npm run dev
```

## What it does

### Pipeline structure and hyperparameters

The pipeline canvas is [React Flow](https://reactflow.dev) with a dagre layout, zoom, pan
and a minimap. Each node is a card showing the operation, its category, and the
hyperparameters that differ from FEDOT's defaults — so a composed pipeline is readable
without opening every node.

The hyperparameter editor is generated from what FEDOT itself publishes:

| Source | What it gives the UI |
| --- | --- |
| `PipelineSearchSpace` | parameter type (`continuous` / `discrete` / `categorical` / nested), sampling scope, hyperopt distribution |
| `default_operation_params.json` | the default value applied to a new node |
| `model_repository.json`, `data_operation_repository.json` | tags, supported tasks, input/output data types |

So a continuous parameter gets a slider bounded by the same range the tuner searches
(logarithmic when the distribution is `loguniform`), a discrete one gets an integer
control, and a categorical one gets a dropdown of the actual admissible values. Values
that differ from the default are marked, and can be reset individually.

Nested search spaces — `glm`, where `family` and `link` are chosen together — are decoded
into variant selectors rather than shown as opaque text.

### Discovering differential equations

A second mode drives [EPDE](https://github.com/ITMO-NSS-team/EPDE), which searches for
the differential equation a field obeys instead of the pipeline that predicts it. It is a
separate distribution with its own dependencies, its own workspace and its own database —
FEDOT.Web mounts it at `/api/epde` when it is installed and does not depend on it, so an
installation that only wants AutoML never pulls in torch. The navigation entry appears
only when the server reports the module as present.

```bash
pip install -e epde-backend
pip install epde        # or from source, see epde-backend/README.md
```

The screens mirror the AutoML ones — upload data, configure a search, watch it live,
read the genealogy — but two things underneath are genuinely different, and
`epde-backend/README.md` is where they are explained:

* **EPDE does not use GOLEM.** Everything the history view gets for free from GOLEM —
  an individual with a uid, its parents, the operator that produced it, a
  per-generation callback, a saved `OptHistory` — has no counterpart in EPDE, whose
  optimisers pass bare systems around and keep only the current population. The
  adapters in `epdeweb/adapters/` supply each of those: identity survives the
  `deepcopy` EPDE breeds with, the per-generation hook is recovered by counting
  MOEA/D sector runs against its weight vectors, and the module writes its own
  history file because there is none to load.
* **There is no single best.** EPDE minimises a vector — the discrepancy of each
  equation against its complexity, or against the stability of its coefficients — so
  every place the AutoML history takes a minimum, this takes a Pareto front. The
  genealogy draws the ancestry of the whole final front, because the interesting
  candidate is often the one slightly worse and much simpler.

The result screen shows the equation typeset (`∂²u/∂x² = −9.849·u`), the trade-off
front, and a per-term ablation: how much of the left-hand side would be left
unexplained with each term removed. That last one needs no refit — an equation is
linear in its coefficients — which is why it is exact rather than sampled.

### The evolution history as a graph — live

A fitness curve shows *that* the population improved. The history graph shows *how*: it
is the genealogy of the run, and it is drawn **while the run is still going**, not only
after it finishes.

That distinction is what makes it a monitoring view. The saved `OptHistory` only exists
once FEDOT returns, so a graph that waited for it would show nothing until the end.
Instead the worker sends a `population` event from GOLEM's iteration callback each
generation — every individual's uid, fitness, operations, pipeline structure and the
operators that produced it — and the backend assembles the genealogy from those. When
the run finishes, the same endpoint switches to the saved history; the response says
which source it used (`source: "live" | "history"`).

Both paths feed the same builder (`fedotweb/history/model.py`), so the graph you watch
during a run and the one you read afterwards are the same drawing rather than two
implementations that drift. While live, there is no final choice yet, so the leader is
marked as *best so far* and the ancestry shown is the ancestry of whatever is winning at
that moment — it re-roots as the leader changes.

The graph is layered — generation `g` occupies layer `2g`, and the mutations and
crossovers that produced generation `g` sit on layer `2g-1` — so it reads top to bottom
with each generation on its own labelled row. Individuals are pipelines, coloured by how
their fitness compares to the rest of the run; operators are the junctions where one
pipeline became another. A pipeline that survives selection unchanged is joined to its
copy in the next generation with a dashed edge, so a surviving line reads as an unbroken
vertical run.

By default only the ancestry of the final choice is drawn, because that is the story:
which crossings and mutations actually led to the returned model. A toggle switches to
the whole population — for a run of 14 generations at population 20 that is roughly 440
nodes, which the canvas handles, but the lineage is what carries the meaning.

Clicking any individual loads the pipeline it stands for and shows it in the same editor
canvas, with the same typed hyperparameter inspector — so you can see exactly which
values evolution settled on at that point, and copy the pipeline into the editor.

Because the layers are known in advance, the layout is computed directly rather than
handed to a general graph layout: rows are placed by layer, and only the order *within*
each row is solved, using the barycentre heuristic to cut edge crossings. That keeps
generations exactly aligned, which is the point of reading the graph vertically.

Two details the graph is careful about, because both are easy to get subtly wrong:

* GOLEM stores the seed populations (`initial_assumptions`, `extended_initial_assumptions`)
  and the result (`final_choices`) as generations of their own. A run that reports ten
  stored generations may have evolved only seven times. Those rows are labelled and
  styled differently, and the generation count reflects evolution only.
* An individual can leave a population and return — elitism reintroduces archived
  graphs — so a parent is not always recorded in the generation immediately before its
  child. Ancestry is resolved against the most recent earlier generation rather than
  only the previous one; otherwise the returning pipeline appears with no incoming edge,
  as if it came from nowhere. Generations that contributed nothing to the shown graph get
  a labelled empty row so the numbering stays continuous.
* GOLEM exposes two generation counters that are offset by one: the optimiser's
  `current_generation_num` starts at one, while `native_generation` on an individual
  starts at zero. Deciding which generation "owns" an individual by comparing those two
  silently drops every operator, leaving a genealogy of nothing but survival edges. The
  builder instead treats the generation where an individual *first appears* as the one
  that draws its operators, which needs no counter at all and is correct for both
  sources.

`GET /api/runs/{uid}/lineage` returns the graph; `GET /api/runs/{uid}/lineage/{individual}`
returns one individual's pipeline.

### Where the score came from

A run reports one number per metric. The **Objective** window on the results panel
shows how that number was arrived at: the metric on every cross-validation fold, their
mean — which *is* the fitness evolution compared pipelines by — the spread across folds,
and the same pipeline scored once on the holdout.

FEDOT averages the per-fold metrics and keeps only the average; the folds behind it are
discarded, so they are recomputed on the same split `DataSourceSplitter` gives the
composer. That the mean equals the arithmetic mean of the folds shown is asserted in the
tests, because it is the whole claim the window makes.

Values are shown as they read normally. FEDOT stores metrics it maximises negated, so
ROC AUC lives internally as `-0.97`; both forms are in the payload, and which is which
is derived from the metric itself — `from_maximised_metric` wraps with `functools.wraps`,
so the wrapper carries `__wrapped__` and metrics that are already minimised do not.

### What the pipeline rests on

The **Sensitivity** window runs GOLEM's own structural analysis: each node is deleted,
replaced and has its subtree removed; each edge is deleted and replaced. Every variant is
refitted and rescored, and the result is a score ratio that GOLEM sign-normalises
(`_compare_with_origin_by_metric` flips numerator and denominator by the metric's sign),
so it reads the same for maximised and minimised metrics: **above 1 the change improved
the objective** — that part is dead weight or replaceable — and below 1 the pipeline
relies on it. That is also how GOLEM's own `optimize()` consumes these numbers: it
applies a change when the ratio exceeds 1. The backend ships the verdict per entity
(`improves`), so clients never re-derive the convention.

Two things were needed to drive it. GOLEM's node and edge analyses fan out over a
`multiprocessing.Pool` even for a single job, so the objective is pickled and shipped to
each worker — that rules out a closure, and rules out defining it in the module run with
`-m`, whose classes pickle against `__main__`; hence `analysis/scoring.py`. And the
analysis works in GOLEM's graph space, not on a FEDOT pipeline, so the graph is adapted
with `PipelineAdapter` going in and restored coming back. (The example in the FEDOT repo
still calls the old signature and carries a `TODO` saying it needs fixing.)

Both analyses refit pipelines many times, so they run out of process and are polled for;
the most recent finished result for a run is reused rather than recomputed on reopening.

### What happens to the data before the pipeline

A pipeline graph is only half the story: FEDOT rewrites the input first. The
**Preprocessing** panel on a dataset runs the framework's own preprocessor and reports,
per column, the types actually found in the file, how many gaps there were, and the type
the pipeline finally receives — plus the decisions behind any change.

On the sample data this immediately shows something the graph never would: `x3`, a column
of integers 0–3, arrives at the pipeline as `str`, because FEDOT reads a numeric column
with fewer than 13 distinct values as categorical. Columns dropped as almost entirely
empty (over 90% gaps), columns dropped for irreconcilable types, failed numeric
conversions and the chosen encoders are all listed the same way.

Index bookkeeping is the subtle part: the gap filter drops columns first, and the type
corrector then works on the filtered matrix, so every index it reports is a position in
that matrix, not in the file. The report maps everything back to file columns — otherwise
one dropped column would silently shift the labels of every column after it.

### Watching a run you started yourself

The GUI does not have to be the thing that launches FEDOT. Add one import to your own
script and the browser opens on the run as it starts:

```python
import fedotweb.autowatch          # noqa: F401

from fedot import Fedot
Fedot(problem='classification', timeout=10).fit(features='data.csv', target='target')
```

The import wraps `Fedot.fit`: the server comes up in a background thread if nothing is
already serving, the run is registered, a tab opens on its page, and every generation is
reported there — same fitness curve, same live genealogy, same controls. An already
running server is reused, so several scripts can report into one GUI. If you passed your
own `optimizer=`, this stays out of the way.

For more control, or to name the run:

```python
from fedot import Fedot
from fedotweb import watch

with watch('sea level forecast') as session:
    model = Fedot(problem='ts_forecasting', timeout=10, optimizer=session.optimizer)
    model.fit(train)
    model.predict(test)
    session.record_result(model)      # optional: stores the pipeline and its metrics
```

`record_result` only reports metrics when the model has actually predicted something.
Calling `get_metrics()` after a bare `fit` returns a number that looks like a score and
means nothing, and a misleading metric is worse than a missing one.

On a headless machine set `FEDOTWEB_AUTOWATCH_BROWSER=0`, or pass
`open_browser=False`; the run is still recorded and the URL still printed.
See `backend/examples/watch_a_script.py`.

### Steering the evolution while it runs

A live run has a control panel: population size, generation limit, time budget, and the
mutation and crossover probabilities. Changes are picked up between generations, so a
generation already in flight is never disturbed — which is why a change appears in "in
force" one generation after you make it. Clearing a field hands that parameter back to
GOLEM's own adaptive policy.

There is also **Finish now**, which is not the same as **Stop**. Stop kills the worker
and throws away whatever it had. Finish now lowers the generation limit so the optimiser
returns through its normal path: FEDOT still fits the best pipeline it found and the run
ends with a result and metrics. In practice it takes effect within seconds.

Getting this to work needed care, because GOLEM re-derives some of these values itself.
`_update_requirements` runs at the start of every generation and overwrites `pop_size`
and both operator probabilities from adaptive sources, so assigning to those fields from
outside would last exactly until the next generation began. The controls therefore work
at the source: those two are supplied by objects implementing GOLEM's `AdaptiveParameter`
protocol, and `fedotweb/runs/control.py` wraps them so an override survives the update —
while still advancing the wrapped policy underneath, so releasing an override resumes the
adaptive schedule rather than freezing it. The generation limit and the time budget are
read live by the stopping conditions and can simply be assigned.

The GUI and the worker are separate processes, so requests travel through a small JSON
file in the run directory. `PATCH /api/runs/{uid}/controls` writes it; `GET` returns both
what was asked for and what the optimiser is actually using.

### Controlling the framework

* Upload a CSV, inspect inferred column types, choose a target.
* Configure a run: task, preset, metric, time budget, population size, generations,
  depth, arity, CV folds, early stopping, parallelism, seed, tuning on/off.
* Optionally start evolution from a pipeline you drew, instead of FEDOT's default
  assumption.
* Watch generations arrive live over a WebSocket: best/mean fitness, population spread,
  and the current best pipeline drawn on the canvas.
* Stop a run; the whole process tree is terminated.
* Metrics are computed on a holdout split the composer never saw.

Runs execute in their own process, so the API stays responsive and cancellation is
reliable. Progress comes from GOLEM's `set_iteration_callback`, which fires as each
generation is recorded — not from parsing logs, and not by waiting for the final history.

## Configuration

All settings are environment variables prefixed with `FEDOTWEB_`, or entries in a `.env`
file.

| Variable | Default | Meaning |
| --- | --- | --- |
| `FEDOTWEB_WORKSPACE` | `~/.fedot-web` | datasets, run artefacts and the SQLite database |
| `FEDOTWEB_HOST` / `FEDOTWEB_PORT` | `127.0.0.1` / `8000` | bind address |
| `FEDOTWEB_MAX_CONCURRENT_RUNS` | `2` | how many compositions may run at once |
| `FEDOTWEB_MAX_RUN_TIMEOUT_MINUTES` | `240` | ceiling on a run's time budget |
| `FEDOTWEB_MAX_UPLOAD_MB` | `256` | largest accepted dataset |
| `FEDOTWEB_CORS_ORIGINS` | Vite dev server | additional allowed origins |
| `FEDOTWEB_STATIC_DIR` | `ui/dist` | built frontend to serve at `/` |
| `FEDOTWEB_MONGO_URI` | unset | optional; SQLite is used when absent |

## Tests

```bash
pytest backend/tests
```

The optional EPDE module has its own suite, which runs without EPDE installed:

```bash
pytest epde-backend/tests -m "not slow"
```

`test_catalog.py` and `test_convert.py` are fast unit tests. `test_run_flow.py` is an
end-to-end test that uploads a dataset and runs a real (short) composition; it takes
about a minute.

```bash
cd ui && npm run typecheck && npm run build
```

## What changed from version 1

| | v1 | v2 |
| --- | --- | --- |
| Backend | Flask 2.2 + flask-restx | FastAPI, OpenAPI, pydantic v2 |
| Storage | MongoDB required to start | SQLite by default, Mongo optional |
| Frontend | React 17, Material-UI v4, Redux, CRA | React 19, MUI v7, Zustand + TanStack Query, Vite |
| Pipeline canvas | dagre-d3, zoom commented out | React Flow: zoom, pan, minimap, layout toggle |
| Node rendering | circle labelled `name id:0` | card with category, tags and live hyperparameters |
| Hyperparameters | free-text key/value pairs | typed controls bounded by FEDOT's search space |
| Validation | `verify_pipeline` with no task | task-aware rules, readable messages |
| Running FEDOT | only pre-seeded showcase cases | upload data and configure a run from the UI |
| Progress | none | per-generation streaming over WebSocket |
| History graph | dagre-d3, individuals labelled `ind_3_7` | layered genealogy, live during the run; click a node for its pipeline and hyperparameters |
| Scripted runs | not possible — the GUI owned the run | `import fedotweb.autowatch` and your own script opens the GUI |
| Mid-run control | none | population size, generations, budget, operator probabilities, graceful finish |
| Objective detail | one averaged number | per-fold metrics, their mean and spread, plus the holdout |
| Preprocessing | invisible | per-column source and final types, and every decision behind a change |
| Sensitivity | not exposed | GOLEM's structural analysis on demand, per node and edge |
| FEDOT | pinned to 0.7.3.1 | master, current node API |
| Equation discovery | not supported | optional EPDE module, with its own adapters in place of GOLEM |

### Notes on the port

* `PrimaryNode` / `SecondaryNode` are deprecated in current FEDOT; conversion now builds
  `PipelineNode` in topological order. The previous implementation rebuilt parents
  recursively and de-duplicated them by `descriptive_id`, which merged distinct nodes
  that happened to look alike — a pipeline with two identical parallel branches came back
  with the wrong topology. There is a regression test for this
  (`test_identical_parallel_branches_are_not_merged`).
* Flask's `@app.before_first_request`, used by the v1 app factory, was removed in
  Flask 2.3 — one reason an in-place dependency bump was not viable.
* Node dimensions and handle geometry are declared to React Flow up front rather than
  measured, so edges are routed on the first render.

## Why FEDOT is installed from master

The **released** FEDOT 0.7.5 wheel on PyPI pins `thegolem==0.4.1` and calls
`log.warning(..., raise_if_test=True, exc=error)` in several error paths — invalid
fitness during evaluation, cache read failures. Neither GOLEM 0.4.1 nor 0.4.2 accepts
those keywords, so they reach `logging.Logger._log` and raise `TypeError`. A composition
then dies at the first pipeline that scores badly, which is an ordinary event during
evolution, not a fatal one. It is invisible with the `fast_train` preset and reliably
reproducible with `best_quality`.

FEDOT **master** has removed those calls and requires `thegolem==0.4.2`, so installing
from master fixes it:

```bash
pip install git+https://github.com/aimclub/FEDOT.git@master
```

`fedotweb/runs/worker.py` still carries a defensive shim (`_patch_logger_kwargs`) that
folds unsupported logging keywords into the message text. On master it finds nothing to
do; it exists so that a user who installs the PyPI release instead of master gets a
warning rather than a dead run. It can be deleted once a release ships the fix.

## Known limitations

* FEDOT skips evolution entirely when the time budget is too small to evaluate a
  generation. The run then returns the initial assumption; the UI says so explicitly in
  the log, but there is no way to know the threshold before starting.
* Authentication was dropped. v1 shipped a `guest`/`guest` account and a login page; v2
  binds to localhost and has no user model. Do not expose it to a network as-is.
