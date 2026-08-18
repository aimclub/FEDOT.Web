"""The objective structural analysis scores candidate pipelines with.

GOLEM's node and edge analyses fan out over a ``multiprocessing.Pool`` — even for
a single job — so the objective is pickled and shipped to each worker. That rules
out a closure, and it rules out defining this in the module executed with ``-m``,
whose classes pickle against ``__main__``. Hence a plain, importable class.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class HoldoutScorer:
    """Fit a candidate pipeline on the training split, score it on the holdout.

    Structural analysis refits the pipeline once per variant it tries, so a single
    holdout keeps the cost linear in the number of variants; cross-validating each
    one would multiply it by the fold count.
    """

    def __init__(
        self,
        train_data: Any,
        holdout_data: Any,
        metric_id: str,
        validation_blocks: int | None = None,
    ) -> None:
        self.train_data = train_data
        self.holdout_data = holdout_data
        self.metric_id = metric_id
        self.validation_blocks = validation_blocks

    def __call__(self, graph: Any) -> float:
        from fedot.core.pipelines.adapters import PipelineAdapter
        from fedot.core.repository.metrics_repository import MetricsRepository

        from .worker import metric_enum

        metric = MetricsRepository.get_metric(metric_enum(self.metric_id))

        # Structural analysis works in GOLEM's own graph space, so what arrives
        # here is an `OptGraph`; it has to be restored before FEDOT can fit it.
        # The analysis is still using the graph it handed over, hence the copy.
        candidate = PipelineAdapter().restore(deepcopy(graph))
        try:
            candidate.fit(self.train_data)
            return float(metric(candidate, self.holdout_data, self.validation_blocks))
        finally:
            try:
                candidate.unfit()
            except Exception:
                pass
