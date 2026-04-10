"""
Canonical nuclide record schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import (
    SchemaValidationError,
    SourcePointer,
    require_non_empty,
    require_non_negative,
)


@dataclass(frozen=True, slots=True)
class NuclideRecord:
    """
    Canonical nuclide record.

    This schema is intentionally conservative. It stores directly identified
    nuclide facts and nearby metadata needed for normalization, downstream
    joins, and later uncertainty propagation.
    """

    nuclide_id: str
    element_symbol: str
    atomic_number_z: int
    neutron_number_n: int
    mass_number_a: int
    isomer_label: str = "ground"
    half_life_seconds: float | None = None
    half_life_uncertainty_seconds: float | None = None
    is_evaluated: bool = True
    source_pointer: SourcePointer = field(
        default_factory=lambda: SourcePointer(
            source_name="unassigned",
            source_record_id="unassigned",
        )
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "nuclide_id", require_non_empty(self.nuclide_id, "nuclide_id")
        )
        object.__setattr__(
            self,
            "element_symbol",
            require_non_empty(self.element_symbol, "element_symbol"),
        )

        z_value = int(self.atomic_number_z)
        n_value = int(self.neutron_number_n)
        a_value = int(self.mass_number_a)

        if z_value <= 0:
            raise SchemaValidationError("atomic_number_z must be positive.")
        if n_value < 0:
            raise SchemaValidationError("neutron_number_n must be zero or positive.")
        if a_value <= 0:
            raise SchemaValidationError("mass_number_a must be positive.")
        if z_value + n_value != a_value:
            raise SchemaValidationError(
                "mass_number_a must equal atomic_number_z + neutron_number_n."
            )

        object.__setattr__(self, "atomic_number_z", z_value)
        object.__setattr__(self, "neutron_number_n", n_value)
        object.__setattr__(self, "mass_number_a", a_value)
        object.__setattr__(
            self, "isomer_label", require_non_empty(self.isomer_label, "isomer_label")
        )

        if self.half_life_seconds is not None:
            object.__setattr__(
                self,
                "half_life_seconds",
                require_non_negative(self.half_life_seconds, "half_life_seconds"),
            )

        if self.half_life_uncertainty_seconds is not None:
            object.__setattr__(
                self,
                "half_life_uncertainty_seconds",
                require_non_negative(
                    self.half_life_uncertainty_seconds,
                    "half_life_uncertainty_seconds",
                ),
            )
            if self.half_life_seconds is None:
                raise SchemaValidationError(
                    "half_life_uncertainty_seconds requires half_life_seconds."
                )
