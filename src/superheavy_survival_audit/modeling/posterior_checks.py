"""
Posterior predictive checks and calibration summaries for survival-audit weights.

This module performs repository-defined internal checks on the Bayesian
survival-audit coefficient layer. It does not validate physical truth. It asks
narrower questions such as:

- where does a reference score sit inside the sampled posterior score distribution?
- is the reference score covered by the central predictive interval?
- how large is the gap between the posterior mean score and the reference score?
- how wide is the predictive interval under the current posterior assumptions?

By default, the reference score is the baseline survival-audit composite score.
That makes this an internal calibration/stability diagnostic rather than an
external experimental validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_non_negative,
    require_probability,
)

from .bayesian_weights import (
    SurvivalComponentPosterior,
    SurvivalComponentPrior,
    score_bayesian_survival_audit,
)
from .monte_carlo import _quantile, _sample_dirichlet
from .survival import SurvivalAuditScore

_COMPONENT_NAMES: tuple[str, ...] = (
    "half_life_support",
    "daughter_resolution_fraction",
    "alpha_continuity_fraction",
    "q_value_coverage_fraction",
    "low_competition_fraction",
)


def _clamp_unit_interval(value: float) -> float:
    """Clamp a numeric value into the closed interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass(frozen=True, slots=True)
class PosteriorPredictiveSummary:
    """
    Posterior predictive summary for the Bayesian survival-audit score layer.
    """

    nuclide_id: str
    sample_count: int
    seed: int
    evidence_strength: float
    reference_score: float
    posterior_mean_score: float
    predictive_mean_score: float
    predictive_lower_score: float
    predictive_median_score: float
    predictive_upper_score: float
    predictive_interval_width: float
    reference_percentile: float
    calibration_gap: float
    is_reference_within_interval: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nuclide_id",
            require_non_empty(self.nuclide_id, "nuclide_id"),
        )

        if int(self.sample_count) <= 0:
            raise SchemaValidationError("sample_count must be greater than zero.")
        object.__setattr__(self, "sample_count", int(self.sample_count))
        object.__setattr__(self, "seed", int(self.seed))
        object.__setattr__(
            self,
            "evidence_strength",
            require_non_negative(self.evidence_strength, "evidence_strength"),
        )
        object.__setattr__(
            self,
            "reference_score",
            require_probability(self.reference_score, "reference_score"),
        )
        object.__setattr__(
            self,
            "posterior_mean_score",
            require_probability(self.posterior_mean_score, "posterior_mean_score"),
        )
        object.__setattr__(
            self,
            "predictive_mean_score",
            require_probability(self.predictive_mean_score, "predictive_mean_score"),
        )
        object.__setattr__(
            self,
            "predictive_lower_score",
            require_probability(
                self.predictive_lower_score,
                "predictive_lower_score",
            ),
        )
        object.__setattr__(
            self,
            "predictive_median_score",
            require_probability(
                self.predictive_median_score,
                "predictive_median_score",
            ),
        )
        object.__setattr__(
            self,
            "predictive_upper_score",
            require_probability(
                self.predictive_upper_score,
                "predictive_upper_score",
            ),
        )
        object.__setattr__(
            self,
            "predictive_interval_width",
            require_non_negative(
                self.predictive_interval_width,
                "predictive_interval_width",
            ),
        )
        object.__setattr__(
            self,
            "reference_percentile",
            require_probability(
                self.reference_percentile,
                "reference_percentile",
            ),
        )
        object.__setattr__(
            self,
            "calibration_gap",
            require_non_negative(self.calibration_gap, "calibration_gap"),
        )

        if self.predictive_lower_score > self.predictive_median_score:
            raise SchemaValidationError(
                "predictive_lower_score must not exceed predictive_median_score."
            )
        if self.predictive_median_score > self.predictive_upper_score:
            raise SchemaValidationError(
                "predictive_median_score must not exceed predictive_upper_score."
            )


def _compute_reference_percentile(
    sorted_scores: list[float],
    reference_score: float,
) -> float:
    """
    Compute the empirical percentile of a reference score within sorted samples.
    """
    if not sorted_scores:
        raise SchemaValidationError("Cannot compute percentile from an empty list.")

    count_at_or_below = sum(1 for score in sorted_scores if score <= reference_score)
    return _clamp_unit_interval(count_at_or_below / len(sorted_scores))


def run_survival_posterior_predictive_check(
    baseline_score: SurvivalAuditScore,
    *,
    prior: SurvivalComponentPrior | None = None,
    evidence_strength: float = 10.0,
    sample_count: int = 2000,
    seed: int = 42,
    reference_score: float | None = None,
    interval_mass: float = 0.90,
) -> PosteriorPredictiveSummary:
    """
    Run a posterior predictive check on the Bayesian survival-audit weight model.

    Steps:
    1. Build the Bayesian posterior over component weights.
    2. Sample score draws from the corresponding Dirichlet weight posterior.
    3. Compare a reference score to the sampled predictive distribution.
    4. Report interval coverage, percentile rank, and calibration gap.

    By default, reference_score is baseline_score.composite_score.
    """
    if sample_count <= 0:
        raise SchemaValidationError("sample_count must be greater than zero.")
    if interval_mass <= 0.0 or interval_mass >= 1.0:
        raise SchemaValidationError("interval_mass must lie strictly between 0 and 1.")

    posterior = score_bayesian_survival_audit(
        baseline_score,
        prior=prior,
        evidence_strength=evidence_strength,
    )
    target_score = (
        baseline_score.composite_score if reference_score is None else reference_score
    )
    target_score = require_probability(target_score, "reference_score")

    return summarize_survival_posterior_predictive_check(
        posterior,
        sample_count=sample_count,
        seed=seed,
        reference_score=target_score,
        interval_mass=interval_mass,
    )


def summarize_survival_posterior_predictive_check(
    posterior: SurvivalComponentPosterior,
    *,
    sample_count: int,
    seed: int,
    reference_score: float,
    interval_mass: float = 0.90,
) -> PosteriorPredictiveSummary:
    """
    Summarize posterior predictive behavior from an existing posterior.
    """
    if sample_count <= 0:
        raise SchemaValidationError("sample_count must be greater than zero.")
    if interval_mass <= 0.0 or interval_mass >= 1.0:
        raise SchemaValidationError("interval_mass must lie strictly between 0 and 1.")

    reference_score = require_probability(reference_score, "reference_score")

    rng = Random(seed)
    alpha_values = [posterior.posterior_alphas[name] for name in _COMPONENT_NAMES]
    component_values = posterior.component_values

    sampled_scores: list[float] = []
    for _ in range(sample_count):
        sampled_weights = _sample_dirichlet(alpha_values, rng=rng)
        sampled_score = sum(
            weight * component_values[name]
            for name, weight in zip(_COMPONENT_NAMES, sampled_weights)
        )
        sampled_scores.append(_clamp_unit_interval(sampled_score))

    sorted_scores = sorted(sampled_scores)
    tail_mass = (1.0 - interval_mass) / 2.0
    lower_score = _quantile(sorted_scores, tail_mass)
    median_score = _quantile(sorted_scores, 0.50)
    upper_score = _quantile(sorted_scores, 1.0 - tail_mass)
    interval_width = upper_score - lower_score

    reference_percentile = _compute_reference_percentile(sorted_scores, reference_score)
    predictive_mean_score = sum(sampled_scores) / len(sampled_scores)
    calibration_gap = abs(posterior.posterior_weighted_score - reference_score)
    within_interval = lower_score <= reference_score <= upper_score

    return PosteriorPredictiveSummary(
        nuclide_id=posterior.nuclide_id,
        sample_count=sample_count,
        seed=seed,
        evidence_strength=posterior.evidence_strength,
        reference_score=reference_score,
        posterior_mean_score=posterior.posterior_weighted_score,
        predictive_mean_score=predictive_mean_score,
        predictive_lower_score=lower_score,
        predictive_median_score=median_score,
        predictive_upper_score=upper_score,
        predictive_interval_width=interval_width,
        reference_percentile=reference_percentile,
        calibration_gap=calibration_gap,
        is_reference_within_interval=within_interval,
    )
