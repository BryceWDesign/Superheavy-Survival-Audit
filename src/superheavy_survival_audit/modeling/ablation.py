"""
Leave-one-term-out ablation analysis for survival-audit components.

This module measures how much the Bayesian survival-audit score changes when one
component is removed and the remaining posterior mean weights are renormalized.

Important boundaries:
- this is a repository-defined sensitivity tool
- it does not infer causal physical truth
- it shows dependence of the current scoring layer on its component structure

Interpretation:
- larger score_drop values indicate stronger dependence on that component under
  the current baseline values and posterior mean weights
- a zero score_drop does not prove a component is physically unimportant; it
  only shows limited influence within this scoring setup
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_probability,
)

from .bayesian_weights import (
    SurvivalComponentPosterior,
    SurvivalComponentPrior,
    score_bayesian_survival_audit,
)
from .survival import SurvivalAuditScore

_COMPONENT_NAMES: Final[tuple[str, ...]] = (
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
class SurvivalComponentAblation:
    """
    Leave-one-term-out ablation result for a single component.
    """

    component_name: str
    retained_weight_sum: float
    ablated_score: float
    score_drop: float
    normalized_remaining_weights: dict[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "component_name",
            require_non_empty(self.component_name, "component_name"),
        )
        if self.component_name not in _COMPONENT_NAMES:
            raise SchemaValidationError(
                f"Unsupported component_name: {self.component_name}"
            )

        object.__setattr__(
            self,
            "retained_weight_sum",
            require_probability(self.retained_weight_sum, "retained_weight_sum"),
        )
        object.__setattr__(
            self,
            "ablated_score",
            require_probability(self.ablated_score, "ablated_score"),
        )
        object.__setattr__(
            self,
            "score_drop",
            require_probability(self.score_drop, "score_drop"),
        )

        if set(self.normalized_remaining_weights) != (
            set(_COMPONENT_NAMES) - {self.component_name}
        ):
            raise SchemaValidationError(
                "normalized_remaining_weights must contain exactly the non-ablated components."
            )

        remaining_sum = 0.0
        for key, value in self.normalized_remaining_weights.items():
            self.normalized_remaining_weights[key] = require_probability(
                value,
                f"normalized_remaining_weights[{key}]",
            )
            remaining_sum += self.normalized_remaining_weights[key]

        if abs(remaining_sum - 1.0) > 1e-9:
            raise SchemaValidationError(
                "normalized_remaining_weights must sum to 1 within numerical tolerance."
            )


@dataclass(frozen=True, slots=True)
class SurvivalAblationSummary:
    """
    Full leave-one-term-out ablation summary for the Bayesian survival-audit layer.
    """

    nuclide_id: str
    posterior_mean_score: float
    component_values: dict[str, float]
    posterior_mean_weights: dict[str, float]
    ablations: tuple[SurvivalComponentAblation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nuclide_id",
            require_non_empty(self.nuclide_id, "nuclide_id"),
        )
        object.__setattr__(
            self,
            "posterior_mean_score",
            require_probability(self.posterior_mean_score, "posterior_mean_score"),
        )

        if set(self.component_values) != set(_COMPONENT_NAMES):
            raise SchemaValidationError(
                "component_values keys do not match expected components."
            )
        if set(self.posterior_mean_weights) != set(_COMPONENT_NAMES):
            raise SchemaValidationError(
                "posterior_mean_weights keys do not match expected components."
            )

        component_sum = 0.0
        for key, value in self.component_values.items():
            self.component_values[key] = require_probability(
                value,
                f"component_values[{key}]",
            )
        for key, value in self.posterior_mean_weights.items():
            self.posterior_mean_weights[key] = require_probability(
                value,
                f"posterior_mean_weights[{key}]",
            )
            component_sum += self.posterior_mean_weights[key]

        if abs(component_sum - 1.0) > 1e-9:
            raise SchemaValidationError(
                "posterior_mean_weights must sum to 1 within numerical tolerance."
            )

        object.__setattr__(self, "ablations", tuple(self.ablations))
        if len(self.ablations) != len(_COMPONENT_NAMES):
            raise SchemaValidationError(
                "ablations must contain one entry for each tracked component."
            )

        ablated_names = {entry.component_name for entry in self.ablations}
        if ablated_names != set(_COMPONENT_NAMES):
            raise SchemaValidationError(
                "ablations do not cover the full component set."
            )

    @property
    def most_influential_component(self) -> SurvivalComponentAblation:
        """
        Return the component ablation with the largest score drop.
        """
        return max(self.ablations, key=lambda entry: entry.score_drop)


def _build_ablation(
    component_name: str,
    posterior: SurvivalComponentPosterior,
) -> SurvivalComponentAblation:
    """
    Build a single leave-one-term-out ablation result.
    """
    posterior_weights = posterior.posterior_mean_weights
    component_values = posterior.component_values

    retained_weight_sum = 1.0 - posterior_weights[component_name]
    if retained_weight_sum <= 0.0:
        raise SchemaValidationError(
            f"Cannot ablate component {component_name} because no weight remains."
        )

    normalized_remaining_weights = {
        key: posterior_weights[key] / retained_weight_sum
        for key in _COMPONENT_NAMES
        if key != component_name
    }

    ablated_score = _clamp_unit_interval(
        sum(
            normalized_remaining_weights[key] * component_values[key]
            for key in normalized_remaining_weights
        )
    )
    score_drop = _clamp_unit_interval(
        max(0.0, posterior.posterior_weighted_score - ablated_score)
    )

    return SurvivalComponentAblation(
        component_name=component_name,
        retained_weight_sum=retained_weight_sum,
        ablated_score=ablated_score,
        score_drop=score_drop,
        normalized_remaining_weights=normalized_remaining_weights,
    )


def run_survival_component_ablation(
    baseline_score: SurvivalAuditScore,
    *,
    prior: SurvivalComponentPrior | None = None,
    evidence_strength: float = 10.0,
) -> SurvivalAblationSummary:
    """
    Run leave-one-term-out ablation on the Bayesian survival-audit layer.
    """
    posterior = score_bayesian_survival_audit(
        baseline_score,
        prior=prior,
        evidence_strength=evidence_strength,
    )
    return summarize_survival_component_ablation(posterior)


def summarize_survival_component_ablation(
    posterior: SurvivalComponentPosterior,
) -> SurvivalAblationSummary:
    """
    Summarize leave-one-term-out ablations from an existing posterior.
    """
    ablations = tuple(
        _build_ablation(component_name, posterior)
        for component_name in _COMPONENT_NAMES
    )

    return SurvivalAblationSummary(
        nuclide_id=posterior.nuclide_id,
        posterior_mean_score=posterior.posterior_weighted_score,
        component_values=dict(posterior.component_values),
        posterior_mean_weights=dict(posterior.posterior_mean_weights),
        ablations=ablations,
    )
