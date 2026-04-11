"""
Monte Carlo sensitivity engine for Bayesian survival-audit weights.

This module samples weight realizations from the Bayesian coefficient layer
using a Dirichlet distribution. It does not claim physical uncertainty bounds.
It produces repository-defined sensitivity summaries for the current surrogate
weight model.

The main purpose is to answer narrower questions such as:
- how wide is the score spread under the current posterior weight uncertainty?
- which component weights move the sampled score most?
- how stable is the posterior-weighted score relative to sampled weight draws?

This is useful for ranking robustness and assumption stress-testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from statistics import mean, pstdev

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
from .survival import SurvivalAuditScore

_COMPONENT_NAMES: tuple[str, ...] = (
    "half_life_support",
    "daughter_resolution_fraction",
    "alpha_continuity_fraction",
    "q_value_coverage_fraction",
    "low_competition_fraction",
)


def _quantile(sorted_values: list[float], q: float) -> float:
    """
    Compute an interpolated quantile for a sorted numeric list.
    """
    if not sorted_values:
        raise SchemaValidationError("Cannot compute a quantile from an empty list.")
    if q < 0.0 or q > 1.0:
        raise SchemaValidationError("Quantile must be between 0 and 1.")

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * q
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index

    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    return lower_value + (fraction * (upper_value - lower_value))


def _sample_dirichlet(
    alpha_values: list[float],
    *,
    rng: Random,
) -> list[float]:
    """
    Sample from a Dirichlet distribution using gamma variates.
    """
    gamma_draws = [rng.gammavariate(alpha, 1.0) for alpha in alpha_values]
    total = sum(gamma_draws)
    if total <= 0.0:
        raise SchemaValidationError("Dirichlet sampling produced a non-positive total.")
    return [draw / total for draw in gamma_draws]


@dataclass(frozen=True, slots=True)
class MonteCarloSensitivitySummary:
    """
    Monte Carlo summary for sampled Bayesian survival-audit weights.
    """

    nuclide_id: str
    sample_count: int
    seed: int
    evidence_strength: float
    posterior_mean_score: float
    monte_carlo_mean_score: float
    monte_carlo_std_score: float
    lower_quantile_score: float
    median_score: float
    upper_quantile_score: float
    min_score: float
    max_score: float
    score_spread: float
    component_mean_weights: dict[str, float]
    component_std_weights: dict[str, float]

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
            "posterior_mean_score",
            require_probability(self.posterior_mean_score, "posterior_mean_score"),
        )
        object.__setattr__(
            self,
            "monte_carlo_mean_score",
            require_probability(self.monte_carlo_mean_score, "monte_carlo_mean_score"),
        )
        object.__setattr__(
            self,
            "monte_carlo_std_score",
            require_non_negative(self.monte_carlo_std_score, "monte_carlo_std_score"),
        )
        object.__setattr__(
            self,
            "lower_quantile_score",
            require_probability(self.lower_quantile_score, "lower_quantile_score"),
        )
        object.__setattr__(
            self,
            "median_score",
            require_probability(self.median_score, "median_score"),
        )
        object.__setattr__(
            self,
            "upper_quantile_score",
            require_probability(self.upper_quantile_score, "upper_quantile_score"),
        )
        object.__setattr__(
            self,
            "min_score",
            require_probability(self.min_score, "min_score"),
        )
        object.__setattr__(
            self,
            "max_score",
            require_probability(self.max_score, "max_score"),
        )
        object.__setattr__(
            self,
            "score_spread",
            require_non_negative(self.score_spread, "score_spread"),
        )

        if not self.component_mean_weights:
            raise SchemaValidationError("component_mean_weights must not be empty.")
        if not self.component_std_weights:
            raise SchemaValidationError("component_std_weights must not be empty.")

        expected_keys = set(_COMPONENT_NAMES)
        if set(self.component_mean_weights) != expected_keys:
            raise SchemaValidationError(
                "component_mean_weights keys do not match expected components."
            )
        if set(self.component_std_weights) != expected_keys:
            raise SchemaValidationError(
                "component_std_weights keys do not match expected components."
            )

        mean_weight_sum = sum(float(value) for value in self.component_mean_weights.values())
        if abs(mean_weight_sum - 1.0) > 1e-6:
            raise SchemaValidationError(
                "component_mean_weights must sum to 1 within numerical tolerance."
            )

        for key, value in self.component_mean_weights.items():
            self.component_mean_weights[key] = require_probability(
                value,
                f"component_mean_weights[{key}]",
            )
        for key, value in self.component_std_weights.items():
            self.component_std_weights[key] = require_non_negative(
                value,
                f"component_std_weights[{key}]",
            )


def run_survival_weight_monte_carlo(
    baseline_score: SurvivalAuditScore,
    *,
    prior: SurvivalComponentPrior | None = None,
    evidence_strength: float = 10.0,
    sample_count: int = 2000,
    seed: int = 42,
) -> MonteCarloSensitivitySummary:
    """
    Run Monte Carlo sampling over the Bayesian survival-audit weight posterior.

    Steps:
    1. Build the posterior alphas using the Bayesian coefficient layer.
    2. Sample Dirichlet weight draws from those posterior alphas.
    3. Compute sampled weighted scores using the baseline component values.
    4. Return a compact summary for downstream robustness analysis.
    """
    if sample_count <= 0:
        raise SchemaValidationError("sample_count must be greater than zero.")

    posterior = score_bayesian_survival_audit(
        baseline_score,
        prior=prior,
        evidence_strength=evidence_strength,
    )
    return _summarize_posterior_samples(
        posterior,
        sample_count=sample_count,
        seed=seed,
    )


def _summarize_posterior_samples(
    posterior: SurvivalComponentPosterior,
    *,
    sample_count: int,
    seed: int,
) -> MonteCarloSensitivitySummary:
    """
    Sample from an existing posterior and summarize the score distribution.
    """
    rng = Random(seed)
    alpha_values = [posterior.posterior_alphas[name] for name in _COMPONENT_NAMES]
    component_values = posterior.component_values

    sampled_scores: list[float] = []
    weight_samples: dict[str, list[float]] = {name: [] for name in _COMPONENT_NAMES}

    for _ in range(sample_count):
        sampled_weights = _sample_dirichlet(alpha_values, rng=rng)

        sampled_score = 0.0
        for name, weight in zip(_COMPONENT_NAMES, sampled_weights):
            weight_samples[name].append(weight)
            sampled_score += weight * component_values[name]
        sampled_scores.append(sampled_score)

    sorted_scores = sorted(sampled_scores)
    component_mean_weights = {
        name: mean(weight_samples[name]) for name in _COMPONENT_NAMES
    }
    component_std_weights = {
        name: pstdev(weight_samples[name]) for name in _COMPONENT_NAMES
    }

    return MonteCarloSensitivitySummary(
        nuclide_id=posterior.nuclide_id,
        sample_count=sample_count,
        seed=seed,
        evidence_strength=posterior.evidence_strength,
        posterior_mean_score=posterior.posterior_weighted_score,
        monte_carlo_mean_score=mean(sampled_scores),
        monte_carlo_std_score=pstdev(sampled_scores),
        lower_quantile_score=_quantile(sorted_scores, 0.05),
        median_score=_quantile(sorted_scores, 0.50),
        upper_quantile_score=_quantile(sorted_scores, 0.95),
        min_score=sorted_scores[0],
        max_score=sorted_scores[-1],
        score_spread=sorted_scores[-1] - sorted_scores[0],
        component_mean_weights=component_mean_weights,
        component_std_weights=component_std_weights,
    )
