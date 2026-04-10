"""
Canonical route record schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import (
    SchemaValidationError,
    SourcePointer,
    require_membership,
    require_non_empty,
    require_non_negative,
)

_ALLOWED_ROUTE_CLASSES = (
    "fusion_evaporation",
    "transfer_reaction",
    "multi_nucleon_transfer",
    "secondary_beam",
    "spallation_derived",
    "unknown",
)

_ALLOWED_FEASIBILITY_CLASSES = (
    "very_low",
    "low",
    "moderate",
    "high",
    "unknown",
)


@dataclass(frozen=True, slots=True)
class RouteRecord:
    """
    Canonical candidate-route schema.

    This is intentionally non-operational. It stores route identity and high-level
    bottleneck metadata without becoming a laboratory instruction record.
    """

    route_id: str
    target_nuclide_id: str
    route_class: str
    descriptor: str
    feasibility_class: str = "unknown"
    bottleneck_penalty: float | None = None
    route_notes: str | None = None
    source_pointer: SourcePointer = field(
        default_factory=lambda: SourcePointer(
            source_name="unassigned",
            source_record_id="unassigned",
        )
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", require_non_empty(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "target_nuclide_id",
            require_non_empty(self.target_nuclide_id, "target_nuclide_id"),
        )
        object.__setattr__(
            self,
            "route_class",
            require_membership(self.route_class, "route_class", _ALLOWED_ROUTE_CLASSES),
        )
        object.__setattr__(
            self,
            "descriptor",
            require_non_empty(self.descriptor, "descriptor"),
        )
        object.__setattr__(
            self,
            "feasibility_class",
            require_membership(
                self.feasibility_class,
                "feasibility_class",
                _ALLOWED_FEASIBILITY_CLASSES,
            ),
        )

        if self.bottleneck_penalty is not None:
            object.__setattr__(
                self,
                "bottleneck_penalty",
                require_non_negative(self.bottleneck_penalty, "bottleneck_penalty"),
            )
            if self.bottleneck_penalty > 1.0:
                raise SchemaValidationError(
                    "bottleneck_penalty must be between 0 and 1 when provided."
                )
