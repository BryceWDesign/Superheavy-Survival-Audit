"""
Bayesian coefficient layer for survival-audit components.

This module adds an explicit prior/posterior layer on top of the baseline
survival-audit score. It does not fit a physics model from raw experiment.
It performs a narrower and more transparent task:

- start from explicit prior weights across already-defined surrogate components
- update those weights using bounded evidence from the baseline component values
- report posterior mean weights and the resulting weighted composite score

Important boundaries:
- this is still a repository-defined surrogate layer
- the posterior here is not a claim about true nuclear-mechanics coefficients
- the update uses pseudo-count logic, not direct experimental likelihoods
- the output is useful for sensitivity-aware ranking, not proof

The five tracked components are:
- half_life_support
- daughter_resolution_fraction
- alpha_continuity_fraction
- q_value_coverage_fraction
- low_competition_fraction
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_non_negative,
    require_probability,
)

from .survival import SurvivalAuditScore

_COMPONENT_NAMES: Final[tuple[str, ...]] = (
    "half_life_support",
    "daughter_resolution_fraction",
    "alpha_continuity_fraction",
    "q_value_coverage_fraction",
    "low_competition_fraction",
)


def _validate_positive_alpha(value: float, field_name: str) -> float:
    """Validate a strictly positive Dirichlet concentration parameter."""
    numeric = float(value)
    if numeric <= 0.0:
        raise SchemaValidationError(f"{field_name} must be greater than zero.")
    return numeric


@dataclass(frozen=True, slots=True)
class SurvivalComponentPrior:
    """
    Dirichlet prior over baseline survival-audit component weights.

    The default values match the initial baseline weighting logic in spirit,
    while making those assumptions explicit and updateable.
    """

    half_life_support_alpha: float = 3.0
    daughter_resolution_alpha: float = 2.0
    alpha_continuity_alpha: float = 2.0
    q_value_coverage_alpha: float = 1.5
    low_competition_alpha: float = 1.5

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "half_life_support_alpha",
            _validate_positive_alpha(
                self.half_life_support_alpha,
                "half_life_support_alpha",
            ),
        )
        object.__setattr__(
            self,
            "daughter_resolution_alpha",
            _validate_positive_alpha(
                self.daughter_resolution_alpha,
                "daughter_resolution_alpha",
            ),
        )
        object.__setattr__(
            self,
            "alpha_continuity_alpha",
            _validate_positive_alpha(
                self.alpha_continuity_alpha,
                "alpha_continuity_alpha",
            ),
        )
        object.__setattr__(
            self,
            "q_value_coverage_alpha",
            _validate_positive_alpha(
                self.q_value_coverage_alpha,
                "q_value_coverage_alpha",
            ),
        )
        object.__setattr__(
            self,
            "low_competition_alpha",
            _validate_positive_alpha(
                self.low_competition_alpha,
                "low_competition_alpha",
            ),
        )

    def as_dict(self) -> dict[str, float]:
        """Return the prior alphas as a named dictionary."""
        return {
            "half_life_support": self.half_life_support_alpha,
            "daughter_resolution_fraction": self.daughter_resolution_alpha,
            "alpha_continuity_fraction": self.alpha_continuity_alpha,
            "q_value_coverage_fraction": self.q_value_coverage_alpha,
            "low_competition_fraction": self.low_competition_alpha,
        }

    @property
    def total_alpha(self) -> float:
        """Return the total prior concentration."""
        return sum(self.as_dict().values())


@dataclass(frozen=True, slots=True)
class SurvivalComponentPosterior:
    """
    Posterior summary for the Bayesian survival-audit coefficient layer.
    """

    nuclide_id: str
    evidence_strength: float
    prior_alphas: dict[str, float]
    posterior_alphas: dict[str, float]
    posterior_mean_weights: dict[str, float]
    component_values: dict[str, float]
    posterior_weighted_score: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nuclide_id",
            require_non_empty(self.nuclide_id, "nuclide_id"),
        )
        object.__setattr__(
            self,
            "evidence_strength",
            require_non_negative(self.evidence_strength, "evidence_strength"),
        )

        if not self.prior_alphas:
            raise SchemaValidationError("prior_alphas must not be empty.")
        if not self.posterior_alphas:
            raise SchemaValidationError("posterior_alphas must not be empty.")
        if not self.posterior_mean_weights:
            raise SchemaValidationError("posterior_mean_weights must not be empty.")
        if not self.component_values:
            raise SchemaValidationError("component_values must not be empty.")

        expected_keys = set(_COMPONENT_NAMES)
        if set(self.prior_alphas) != expected_keys:
            raise SchemaValidationError("prior_alphas keys do not match expected components.")
        if set(self.posterior_alphas) != expected_keys:
            raise SchemaValidationError(
                "posterior_alphas keys do not match expected components."
            )
        if set(self.posterior_mean_weights) != expected_keys:
            raise SchemaValidationError(
                "posterior_mean_weights keys do not match expected components."
            )
        if set(self.component_values) != expected_keys:
            raise SchemaValidationError(
                "component_values keys do not match expected components."
            )

        for key, value in self.prior_alphas.items():
            if float(value) <= 0.0:
                raise SchemaValidationError(f"prior_alphas[{key}] must be greater than zero.")
        for key, value in self.posterior_alphas.items():
            if float(value) <= 0.0:
                raise SchemaValidationError(
                    f"posterior_alphas[{key}] must be greater than zero."
                )
        for key, value in self.posterior_mean_weights.items():
            self.posterior_mean_weights[key] = require_probability(
                value,
                f"posterior_mean_weights[{key}]",
            )
        for key, value in self.component_values.items():
            self.component_values[key] = require_probability(
                value,
                f"component_values[{key}]",
            )

        mean_weight_sum = sum(self.posterior_mean_weights.values())
        if abs(mean_weight_sum - 1.0) > 1e-9:
            raise SchemaValidationError(
                "posterior_mean_weights must sum to 1 within numerical tolerance."
            )

        object.__setattr__(
            self,
            "posterior_weighted_score",
            require_probability(
                self.posterior_weighted_score,
                "posterior_weighted_score",
            ),
        )


def _extract_component_values(
    baseline_score: SurvivalAuditScore,
) -> dict[str, float]:
    """Extract baseline component values as a named dictionary."""
    return {
        "half_life_support": baseline_score.half_life_support,
        "daughter_resolution_fraction": baseline_score.daughter_resolution_fraction,
        "alpha_continuity_fraction": baseline_score.alpha_continuity_fraction,
        "q_value_coverage_fraction": baseline_score.q_value_coverage_fraction,
        "low_competition_fraction": baseline_score.low_competition_fraction,
    }


def score_bayesian_survival_audit(
    baseline_score: SurvivalAuditScore,
    *,
    prior: SurvivalComponentPrior | None = None,
    evidence_strength: float = 10.0,
) -> SurvivalComponentPosterior:
    """
    Update component weights under a Dirichlet pseudo-count model.

    Update rule:
    posterior_alpha_i = prior_alpha_i + evidence_strength * component_value_i

    Posterior mean weight:
    posterior_alpha_i / sum_j posterior_alpha_j

    The weighted posterior score is then the posterior mean weighted average of
    the baseline component values.
    """
    if prior is None:
        prior = SurvivalComponentPrior()

    strength = require_non_negative(evidence_strength, "evidence_strength")
    component_values = _extract_component_values(baseline_score)
    prior_alphas = prior.as_dict()

    posterior_alphas: dict[str, float] = {}
    for key in _COMPONENT_NAMES:
        posterior_alphas[key] = prior_alphas[key] + (strength * component_values[key])

    posterior_total = sum(posterior_alphas.values())
    posterior_mean_weights = {
        key: posterior_alphas[key] / posterior_total for key in _COMPONENT_NAMES
    }

    posterior_weighted_score = sum(
        posterior_mean_weights[key] * component_values[key]
        for key in _COMPONENT_NAMES
    )

    return SurvivalComponentPosterior(
        nuclide_id=baseline_score.nuclide_id,
        evidence_strength=strength,
        prior_alphas=prior_alphas,
        posterior_alphas=posterior_alphas,
        posterior_mean_weights=posterior_mean_weights,
        component_values=component_values,
        posterior_weighted_score=posterior_weighted_score,
    )
