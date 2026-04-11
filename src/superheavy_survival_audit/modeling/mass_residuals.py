"""
Mass-residual consensus layer for AME-aligned comparison.

This module compares an observed AME-style mass record against one or more
reference-model predictions and summarizes the resulting residual structure.

Important boundaries:
- this is not a new mass model
- this does not claim shell closure or physical truth by itself
- this is a comparison layer for agreement, disagreement, and clustering
- the output is intended for audit and prioritization, not proof

The current consensus score rewards:
- low mean absolute residual
- low spread across model residuals
- directional agreement across model residual signs

This creates a compact consensus signal that can later be combined with other
evidence layers without hiding the underlying residual structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Iterable

from superheavy_survival_audit.ingest import AMEMassRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_non_negative,
    require_probability,
)


def _clamp_unit_interval(value: float) -> float:
    """Clamp a numeric value into the closed interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _normalize_penalty(value: float, scale_kev: float) -> float:
    """
    Convert a non-negative residual magnitude into a bounded agreement score.

    Values near zero map toward 1.
    Values at or above the scale map toward 0.
    """
    if scale_kev <= 0.0:
        raise SchemaValidationError("scale_kev must be greater than zero.")
    return _clamp_unit_interval(1.0 - min(value / scale_kev, 1.0))


def _majority_sign_summary(values: list[float]) -> tuple[str, float]:
    """
    Return the majority residual sign label and its agreement fraction.
    """
    if not values:
        raise SchemaValidationError("Cannot summarize signs for an empty value list.")

    counts = {"negative": 0, "zero": 0, "positive": 0}
    for value in values:
        if value < 0.0:
            counts["negative"] += 1
        elif value > 0.0:
            counts["positive"] += 1
        else:
            counts["zero"] += 1

    max_count = max(counts.values())
    labels = [label for label, count in counts.items() if count == max_count]
    if len(labels) == 1:
        label = labels[0]
    else:
        label = "mixed"
    return label, max_count / len(values)


@dataclass(frozen=True, slots=True)
class ReferenceMassPrediction:
    """
    One reference-model mass prediction aligned to an observed nuclide.
    """

    model_name: str
    predicted_mass_excess_kev: float
    model_family: str | None = None
    source_label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "model_name",
            require_non_empty(self.model_name, "model_name"),
        )
        object.__setattr__(
            self,
            "predicted_mass_excess_kev",
            float(self.predicted_mass_excess_kev),
        )

        if self.model_family is not None:
            object.__setattr__(
                self,
                "model_family",
                require_non_empty(self.model_family, "model_family"),
            )
        if self.source_label is not None:
            object.__setattr__(
                self,
                "source_label",
                require_non_empty(self.source_label, "source_label"),
            )


@dataclass(frozen=True, slots=True)
class MassResidualObservation:
    """
    Residual observation for one reference-model prediction.
    """

    model_name: str
    predicted_mass_excess_kev: float
    signed_residual_kev: float
    absolute_residual_kev: float
    model_family: str | None = None
    source_label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "model_name",
            require_non_empty(self.model_name, "model_name"),
        )
        object.__setattr__(
            self,
            "predicted_mass_excess_kev",
            float(self.predicted_mass_excess_kev),
        )
        object.__setattr__(
            self,
            "signed_residual_kev",
            float(self.signed_residual_kev),
        )
        object.__setattr__(
            self,
            "absolute_residual_kev",
            require_non_negative(
                self.absolute_residual_kev,
                "absolute_residual_kev",
            ),
        )

        if self.model_family is not None:
            object.__setattr__(
                self,
                "model_family",
                require_non_empty(self.model_family, "model_family"),
            )
        if self.source_label is not None:
            object.__setattr__(
                self,
                "source_label",
                require_non_empty(self.source_label, "source_label"),
            )


@dataclass(frozen=True, slots=True)
class MassResidualConsensus:
    """
    Consensus summary over reference-model residuals for one observed AME record.
    """

    nuclide_id: str
    observed_mass_excess_kev: float
    model_count: int
    majority_sign_label: str
    sign_agreement_fraction: float
    mean_signed_residual_kev: float
    mean_absolute_residual_kev: float
    residual_std_kev: float
    accuracy_score: float
    spread_score: float
    consensus_score: float
    residual_observations: tuple[MassResidualObservation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nuclide_id",
            require_non_empty(self.nuclide_id, "nuclide_id"),
        )
        object.__setattr__(
            self,
            "observed_mass_excess_kev",
            float(self.observed_mass_excess_kev),
        )

        if int(self.model_count) <= 0:
            raise SchemaValidationError("model_count must be greater than zero.")
        object.__setattr__(self, "model_count", int(self.model_count))

        if self.majority_sign_label not in {"negative", "zero", "positive", "mixed"}:
            raise SchemaValidationError(
                "majority_sign_label must be one of: negative, zero, positive, mixed."
            )

        object.__setattr__(
            self,
            "sign_agreement_fraction",
            require_probability(
                self.sign_agreement_fraction,
                "sign_agreement_fraction",
            ),
        )
        object.__setattr__(
            self,
            "mean_signed_residual_kev",
            float(self.mean_signed_residual_kev),
        )
        object.__setattr__(
            self,
            "mean_absolute_residual_kev",
            require_non_negative(
                self.mean_absolute_residual_kev,
                "mean_absolute_residual_kev",
            ),
        )
        object.__setattr__(
            self,
            "residual_std_kev",
            require_non_negative(self.residual_std_kev, "residual_std_kev"),
        )
        object.__setattr__(
            self,
            "accuracy_score",
            require_probability(self.accuracy_score, "accuracy_score"),
        )
        object.__setattr__(
            self,
            "spread_score",
            require_probability(self.spread_score, "spread_score"),
        )
        object.__setattr__(
            self,
            "consensus_score",
            require_probability(self.consensus_score, "consensus_score"),
        )
        object.__setattr__(
            self,
            "residual_observations",
            tuple(self.residual_observations),
        )

        if len(self.residual_observations) != self.model_count:
            raise SchemaValidationError(
                "residual_observations length must match model_count."
            )


def build_mass_residual_consensus(
    observed_record: AMEMassRecord,
    reference_predictions: Iterable[ReferenceMassPrediction],
    *,
    residual_scale_kev: float = 1000.0,
) -> MassResidualConsensus:
    """
    Build a mass-residual consensus summary from one observed AME record and
    multiple reference-model predictions.

    Scoring notes:
    - accuracy_score = bounded agreement from mean absolute residual
    - spread_score = bounded agreement from residual standard deviation
    - consensus_score = 0.40 * accuracy_score
                        + 0.40 * spread_score
                        + 0.20 * sign_agreement_fraction
    """
    if residual_scale_kev <= 0.0:
        raise SchemaValidationError("residual_scale_kev must be greater than zero.")

    predictions = tuple(reference_predictions)
    if not predictions:
        raise SchemaValidationError("reference_predictions must not be empty.")

    seen_model_names: set[str] = set()
    observations: list[MassResidualObservation] = []
    signed_residuals: list[float] = []
    absolute_residuals: list[float] = []

    for prediction in predictions:
        if prediction.model_name in seen_model_names:
            raise SchemaValidationError(
                f"Duplicate model_name in reference_predictions: {prediction.model_name}"
            )
        seen_model_names.add(prediction.model_name)

        signed_residual = (
            observed_record.mass_excess_kev - prediction.predicted_mass_excess_kev
        )
        absolute_residual = abs(signed_residual)

        observations.append(
            MassResidualObservation(
                model_name=prediction.model_name,
                predicted_mass_excess_kev=prediction.predicted_mass_excess_kev,
                signed_residual_kev=signed_residual,
                absolute_residual_kev=absolute_residual,
                model_family=prediction.model_family,
                source_label=prediction.source_label,
            )
        )
        signed_residuals.append(signed_residual)
        absolute_residuals.append(absolute_residual)

    majority_sign_label, sign_agreement_fraction = _majority_sign_summary(
        signed_residuals
    )
    mean_signed_residual_kev = mean(signed_residuals)
    mean_absolute_residual_kev = mean(absolute_residuals)
    residual_std_kev = pstdev(signed_residuals) if len(signed_residuals) > 1 else 0.0

    accuracy_score = _normalize_penalty(mean_absolute_residual_kev, residual_scale_kev)
    spread_score = _normalize_penalty(residual_std_kev, residual_scale_kev)
    consensus_score = _clamp_unit_interval(
        (0.40 * accuracy_score)
        + (0.40 * spread_score)
        + (0.20 * sign_agreement_fraction)
    )

    return MassResidualConsensus(
        nuclide_id=observed_record.nuclide_id,
        observed_mass_excess_kev=observed_record.mass_excess_kev,
        model_count=len(observations),
        majority_sign_label=majority_sign_label,
        sign_agreement_fraction=sign_agreement_fraction,
        mean_signed_residual_kev=mean_signed_residual_kev,
        mean_absolute_residual_kev=mean_absolute_residual_kev,
        residual_std_kev=residual_std_kev,
        accuracy_score=accuracy_score,
        spread_score=spread_score,
        consensus_score=consensus_score,
        residual_observations=tuple(observations),
    )
