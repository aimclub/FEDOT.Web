# EPDE.Web

A web interface for [EPDE](https://github.com/ITMO-NSS-team/EPDE), which discovers
differential equations from data by evolutionary search.

It ships as a **separate distribution** with a separate workspace and a separate
database. FEDOT.Web mounts it at `/api/epde` when it happens to be installed, and
does not depend on it: an installation that only wants AutoML never sees torch or
scikit-learn. Nothing here imports FEDOT or GOLEM, and the frontend module is a
self-contained directory, so this can be lifted out into its own product without a
migration.

```bash
pip install -e epde-backend[dev]
pip install epde              # or: pip install git+https://github.com/ITMO-NSS-team/EPDE.git
python -m epdeweb             # standalone, on http://127.0.0.1:8010
```

Or mounted inside FEDOT.Web — `pip install -e epde-backend` is enough; the mode
appears in the navigation on the next start.

**Install FEDOT first, then this.** EPDE pulls torch and wants a newer numpy and
scikit-learn than FEDOT pins; adding FEDOT to an environment that already has
EPDE's stack sends pip into a backtracking search that does not finish in any
reasonable time. In the other order it resolves immediately, and EPDE runs
perfectly well on FEDOT's older pins — the module's whole test suite, real
searches included, passes on numpy 1.26 and scikit-learn 1.6.

## Why there is an adapter layer at all

FEDOT.Web draws its evolution history straight out of GOLEM. Every graph GOLEM
evolves is wrapped in an `Individual` carrying a uid, its parents and the operator
that produced it; the optimiser takes an iteration callback; and an `OptHistory` is
saved at the end. The whole genealogy view is three facts and one hook.

**EPDE uses none of that.** Its optimisers pass bare `SoEq` objects around, a
candidate has no more identity than its index in a list, `MOEADDOptimizer.optimize`
runs its epochs to completion without a hook, and when a search finishes all that
exists is the final population. So `epdeweb/adapters/` supplies each missing piece:

| GOLEM provides | `epdeweb/adapters/` supplies |
| --- | --- |
| `Individual.uid` | `individuals.py` — a record written into the candidate's `__dict__` |
| `Individual.parent_individuals` | the same record, read *before* an operator overwrites it |
| `set_iteration_callback` | `observer.py` — counts sector runs against the weight vectors |
| `OptHistory` | `history/service.py` — the module writes its own, in the shape it streams |
| requirements the optimiser re-reads | `controls.py` — writes into the live operators' `params` |

### How ancestry is recovered without an `Individual`

EPDE breeds by `deepcopy`: an offspring is a copy of its parent that is then
modified. A record written into the system's `__dict__` therefore travels into the
copy for free, which makes the parent readable at the exact moment the offspring
comes into existence. `ChromosomeCrossover.apply` and `SystemMutation.apply` are
wrapped to read that inherited record and then overwrite it.

Two details this gets right, because both are silent when wrong:

* An offspring is often crossed **and then** mutated before any population
  contains it. Numbering it twice would put a node in the graph that no generation
  ever held, so a record still awaiting its first population accumulates a *chain*
  of operators under one uid — the shape GOLEM records in
  `operators_from_prev_generation`.
* EPDE copies systems for reasons that are not reproduction. Two live objects then
  claim one uid, and a population holding both would draw one node where there are
  two. Duplicates are separated when the population is read, which is the only
  place the ambiguity is observable.

### How the per-generation hook is installed

`MOEADDSectorProcesser.run` is called exactly once per weight vector, so counting
calls against `len(optimizer.weights)` recovers the epoch boundary in every EPDE
build without depending on anything inside `optimize` — which differs between the
release and master. The single-objective path uses `LinkedBlocks.traversal`, one
call of which is one generation. `InitialParetoLevelSorting.apply` marks where the
seed population is first placed, so generation zero is what the search started
from rather than a population it had already changed.

The wrappers go on the classes, not on instances: EPDE builds its operators deep
inside a strategy director and never hands them out. A worker process runs exactly
one search, so a process-wide patch is exactly scoped, and `uninstall()` puts the
originals back.

## What differs from the AutoML side, and why

**A candidate is a system of equations, not a pipeline.** It is rendered as its
syntax tree — system → equation → term → factor — and, more usefully, as the
equation itself: `∂²u/∂x² = −9.849·u`, typeset from the structured terms.

**There is no single best.** EPDE minimises a *vector*: the discrepancy of each
equation and, on the second axis, either its structural complexity or the
stability of its coefficients. So everywhere FEDOT.Web takes a minimum, this takes
a Pareto front. "The best of this generation" is a set; "the winner" is a set; the
ancestry drawn is the ancestry of that whole set, because a user comparing an
accurate equation against a simple one wants both lines.

**What the answer rests on is cheaper to ask.** GOLEM's structural analysis
deletes each node of a pipeline and refits. An equation is linear in its
coefficients, so the residual with a term removed is read straight off the design
matrix the fit already used — no refit, and it runs in the worker where the token
cache is still alive.

## Version tolerance

EPDE is developed on master well ahead of its PyPI releases, and the differences
land exactly where a GUI touches it. Every call into the framework is filtered
through the signature of the installed build, and anything dropped is reported to
the user rather than raised in their face several seconds into a run.

Three differences are handled explicitly, because each produces *plausible*
output when got wrong rather than an error:

* **Where the intercept lives.** 1.2.17 appends it to `weights_final`; master
  sizes that vector to the coefficients and keeps the intercept in
  `weights_internal[-1]`. Reading master's with the older assumption drops the
  last real coefficient and reports it as a constant — `u_tt = −9.87 u` becomes
  `u_tt = −9.87`. The layout is decided by length against the term count.
* **What `Equation.evaluate` returns.** Master returns `(value, target,
  features)`; earlier releases returned two. Unpacking against the wrong one puts
  the design matrix where the target belongs.
* **What the second Pareto axis measures.** Master can put coefficient stability
  there instead of complexity, chosen by `use_pic`, whose default is `True`. The
  effective value is read back off the constructed search, so a run that does not
  ask still gets its chart labelled correctly.

Axis names are substituted too. EPDE numbers derivative axes positionally and
zero-based, so a wave equation comes back as `d^2u/dx0^2 = d^2u/dx1^2`; the
dataset's own names turn that into `∂²u/∂t² = ∂²u/∂x²`. Getting the base wrong
would swap time and space while still looking like an equation, so it is asserted
in the tests.

## Steering a search while it runs

EPDE has no requirements object to write to; each operator owns a `params` dict it
reads on every application. The controls find the live instances inside the
strategy and assign to them between generations, so a change takes effect on the
next generation and never disturbs one in flight.

Two limits are structural and are stated rather than offered and quietly ignored:

* **Population size is fixed.** MOEA/D pairs every individual with a weight vector
  generated at construction; a new individual would have no sector.
* **The epoch count cannot be lowered inside EPDE.** `optimize` iterates over
  `np.arange(epochs)` captured at entry, so a lower limit is enforced from
  outside — the same distinction FEDOT.Web draws between **Stop** (kill the
  worker, lose the result) and **Finish now** (return through the normal path with
  the population intact).

EPDE also has no time budget of its own. The one in the run configuration is
enforced at generation boundaries, so it ends a run *with* a population rather
than by killing it.

## Data

A search needs a field: one or more variables sampled on a grid, plus the
coordinates of that grid. Uploads may be a `.npy` array, an `.npz` bundle of the
field and its coordinate vectors, or a CSV — either a numeric matrix or a table
with a time column. Everything is normalised to one stored form at upload, where a
wrong guess can still be corrected by hand.

The grid is half the input, not metadata. EPDE differentiates with respect to
these coordinates, so a file that carried only values arrives with axes running
0, 1, 2, … and every first derivative is wrong by the true spacing, every second
by its square. The discovered *structure* survives that; the coefficients do not.
The dataset screen therefore says when coordinates had to be invented, and lets
the real ranges be set.

Four built-in fields are exact solutions of stated equations — wave, heat,
transport and a Lotka-Volterra system — so a run can be judged rather than
admired.

## Configuration

Environment variables prefixed `EPDEWEB_`, or a `.env` file.

| Variable | Default | Meaning |
| --- | --- | --- |
| `EPDEWEB_WORKSPACE` | `~/.epde-web` | fields, run artefacts and the SQLite database |
| `EPDEWEB_HOST` / `EPDEWEB_PORT` | `127.0.0.1` / `8010` | bind address, standalone only |
| `EPDEWEB_MAX_CONCURRENT_RUNS` | `2` | how many searches may run at once |
| `EPDEWEB_MAX_RUN_TIMEOUT_MINUTES` | `240` | ceiling on a run's time budget |
| `EPDEWEB_MAX_UPLOAD_MB` | `512` | largest accepted field |
| `EPDEWEB_MAX_GRID_NODES` | `4000000` | ceiling on one variable's grid |
| `EPDEWEB_CORS_ORIGINS` | Vite dev server | additional allowed origins |
| `EPDEWEB_STATIC_DIR` | `ui/dist` | built frontend to serve at `/` |

The workspace is separate from FEDOT.Web's on purpose: neither application can
corrupt the other's data, and splitting this out later needs no migration.

## Tests

```bash
pytest epde-backend/tests -m "not slow"
```

Everything but `test_run_flow.py` runs without EPDE installed — the adapters are
duck-typed and the instrumentation is exercised against a stand-in `epde` package
with the same module paths. `test_run_flow.py` runs real searches through the API
and takes a couple of minutes; it is skipped automatically when EPDE is missing,
and it is the test that catches what stand-ins cannot: which vector EPDE fills,
which way round its weights are stored, and what its derivative labels mean.

```bash
pytest epde-backend/tests            # includes the end-to-end searches
```

## Known limitations

* The genealogy is only as complete as the operators that were wrapped. A custom
  strategy director that breeds through some other operator will still produce a
  graph, but its offspring appear without ancestry rather than wrongly attributed.
* Per-term ablation is computed once, at the end of a run, for the final front. A
  candidate opened from the genealogy shows its terms and coefficients but no
  ablation: reproducing it would mean rebuilding the whole token pool.
* Multi-variable systems are supported, but EPDE's own single-objective path
  reports one quality value per equation and no complexity axis, so the Pareto
  chart is empty for those runs — the objective curves are not.
* Authentication is not part of this module. It binds to localhost, like the rest
  of FEDOT.Web 2.0.
