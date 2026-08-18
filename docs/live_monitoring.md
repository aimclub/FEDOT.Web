# Live monitoring of a FEDOT run

The GUI does not have to be the thing that launches FEDOT. You keep your own
script, and the interface attaches to it: the server comes up by itself, a
browser tab opens on the run's page, and every generation appears there as the
optimiser works — the fitness curve, the live genealogy and the evolution
controls.

## One-time setup

Install the `fedotweb` package into the same environment your FEDOT scripts
use:

```bash
pip install -e backend
```

For the auto-started server to serve the web pages and share its data with a
server you start by hand, set two environment variables (once, e.g. at the
user level):

```
FEDOTWEB_STATIC_DIR=<repo>/ui/dist
FEDOTWEB_WORKSPACE=<your workspace directory>
```

Without them the API starts without the web pages, and the workspace defaults
to `~/.fedot-web`.

## Option 1 — a single line

Add the import **before** constructing `Fedot`:

```python
import fedotweb.autowatch  # noqa: F401  -- opens the GUI on every fit()

from fedot import Fedot

Fedot(problem='classification', timeout=10).fit(features='data.csv', target='target')
```

The import wraps `Fedot.fit`: when `fit()` is called, the server comes up in a
background thread (an instance already listening on 127.0.0.1:8000 is reused,
so several scripts can report into one GUI), the run is registered, a browser
tab opens, and the evolution is streamed there live. An explicit `optimizer=`
argument of your own is left alone.

## Option 2 — name the run and record the result

```python
from fedot import Fedot
from fedotweb import watch

with watch('my experiment') as session:
    model = Fedot(problem='classification', timeout=10, optimizer=session.optimizer)
    model.fit(features=X, target=y)
    model.predict(X_test)
    session.record_result(model)  # stores the pipeline and its metrics in the GUI
```

`record_result` reports metrics only after a real `predict` — a "metric" taken
after a bare `fit` would look like a score and mean nothing.

## What you get while the run is going

- **The fitness curve** — best-only by default with markers where the leading
  pipeline changed; the tail after the last improvement is hidden, and a
  caption says how many generations were cut.
- **The genealogy** — which pipeline was mutated or crossed into which;
  hovering an operator shows what exactly changed.
- **The control panel** — population size, generation limit, time budget, and
  the mutation and crossover probabilities. Changes are picked up between
  generations; clearing a field hands the parameter back to GOLEM's adaptive
  policy.
- **Finish now** — not the same as Stop: the optimiser returns through its
  normal path, FEDOT still fits the best pipeline it found, and the run ends
  with a result and metrics.

## Notes

- On a headless machine set `FEDOTWEB_AUTOWATCH_BROWSER=0` — no tab opens, but
  the run is still recorded and its URL is printed to the console.
- Your script may exit before the server thread: the run is already persisted,
  nothing is lost.
- A worked example lives in `backend/examples/watch_a_script.py`; see also the
  "Watching a run you started yourself" section of `README.v2.md`.
