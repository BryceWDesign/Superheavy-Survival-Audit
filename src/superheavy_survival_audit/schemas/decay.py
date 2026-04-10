"""
Canonical decay record schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import (
    SchemaValidationError,
    SourcePointer,
    require_membership,
    require_non_empty,
    require_non_negative,
    require_probability,
)

_ALLOWED_DECAY_MODES = (
    "alpha",
    "beta_minus",
    "beta_plus",
    "electron_capture",
    "gamma",
    "isomeric_transition",
    "spontaneous_fission",
    "cluster_decay",
    "unknown",
)


@dataclass(frozen=True, slots=True)
class DecayRecord:
    """
    Canonical decay-event or decay-channel record.

    This schema stores one parent-to-daughter relationship or a parent decay
    mode when the daughter is unknown or unresolved.
    """

    decay_id: str
    parent_nuclide_id: str
    decay_mode: str
    daughter_nuclide_id: str | None = None
    branching_fraction: float | None = None
    branching_uncertainty: float | None = None
    q_value_mev: float | None = None
    q_value_uncertainty_mev: float | None = None
    source_pointer: SourcePointer = field(
        default_factory=lambda: SourcePointer(
            source_name="unassigned",
            source_record_id="unassigned",
        )
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "decay_id", require_non_empty(self.decay_id, "decay_id"))
        object.__setattr__(
            self,
            "parent_nuclide_id",
            require_non_empty(self.parent_nuclide_id, "parent_nuclide_id"),
        )
        object.__setattr__(
            self,
            "decay_mode",
            require_membership(self.decay_mode, "decay_mode", _ALLOWED_DECAY_MODES),
        )

        if self.daughter_nuclide_id is not None:
            object.__setattr__(
                self,
                "daughter_nuclide_id",
                require_non_empty(self.daughter_nuclide_id, "daughter_nuclide_id"),
            )

        if self.branching_fraction is not None:
            object.__setattr__(
                self,
                "branching_fraction",
                require_probability(self.branching_fraction, "branching_fraction"),
            )

        if self.branching_uncertainty is not None:
            object.__setattr__(
                self,
                "branching_uncertainty",
                require_non_negative(
                    self.branching_uncertainty,
                    "branching_uncertainty",
                ),
            )
            if self.branching_fraction is None:
                raise SchemaValidationError(
                    "branching_uncertainty requires branching_fraction."
                )
            if self.branching_fraction + self.branching_uncertainty > 1.0 + 1e-12:
                raise SchemaValidationError(
                    "branching_fraction plus branching_uncertainty cannot exceed 1."
                )

        if self.q_value_mev is not None:
            object.__setattr__(
                self,
                "q_value_mev",
                require_non_negative(self.q_value_mev, "q_value_mev"),
            )

        if self.q_value_uncertainty_mev is not None:
            object.__setattr__(
                self,
                "q_value_uncertainty_mev",
                require_non_negative(
                    self.q_value_uncertainty_mev,
                    "q_value_uncertainty_mev",
                ),
            )
            if self.q_value_mev is None:
                raise SchemaValidationError(
                    "q_value_uncertainty_mev requires q_value_mev."
                )
