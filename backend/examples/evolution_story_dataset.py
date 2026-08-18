"""A dataset on which FEDOT's evolution has a real story to tell.

On most tabular data the evolution history looks trivial, and for a reason:
the initial assumptions already contain catboost, xgboost, lgbm, rf, logit and
a gbm ensemble, each prefixed with data-appropriate preprocessing. There is
usually nothing left to discover.

This generator builds data where every one of those seeds is provably weak and
the strong pipelines are several structural discoveries away:

* the signal is a sum of two squared oblique projections, (w1.x)^2 + (w2.x)^2 —
  linear models are blind to it (AUC ~0.51), and axis-aligned boosting is
  myopic (~0.67), because no single feature carries the signal;
* features are scale-corrupted by up to two orders of magnitude, so distance-
  and gradient-based models additionally need a scaling node in front.

Measured single-pipeline scores on a holdout (n=2000, p=24):

    seeds: gbm_linear 0.671 | rf 0.662 | scaling->logit 0.513
    rungs: scaling->poly_features->logit 0.735
    top:   qda 0.873 | scaling->mlp 0.872

Note: qda and mlp are tagged 'deprecated' and never enter preset candidate
sets; pass them via `available_operations` to make the summit reachable.
"""

import numpy as np
import pandas as pd


def make_evolution_story(n: int = 2000, p: int = 24, hidden: int = 2,
                         noise: float = 0.35, scale_pow: float = 2.0,
                         seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    latent = rng.normal(size=(n, p))

    score = np.zeros(n)
    for _ in range(hidden):
        direction = rng.normal(size=p)
        direction /= np.linalg.norm(direction)
        score += (latent @ direction) ** 2
    score = score - np.median(score)
    score += rng.normal(scale=noise * np.std(score), size=n)

    features = latent * 10 ** rng.uniform(-scale_pow, scale_pow, size=p)
    frame = pd.DataFrame({f"f{i}": features[:, i] for i in range(p)})
    frame["target"] = (score > 0).astype(int)
    return frame


if __name__ == "__main__":
    frame = make_evolution_story()
    frame.to_csv("quadratic_signal.csv", index=False)
    print(f"written quadratic_signal.csv: {frame.shape[0]} rows, "
          f"{frame.shape[1] - 1} features, base rate {frame.target.mean():.2f}")
