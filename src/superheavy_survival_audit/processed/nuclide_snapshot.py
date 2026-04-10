"""
Processed nuclide snapshot model.

This model creates a repository-managed export shape that is explicit about:

- canonical nuclide identity
- upstream source linkage
- uncertainty availability
- snapshot identity
- repository version

The goal is not to replace the canonical schema. The goal is to produce a
stable processed export layer for release-grade comparisons and downstream
artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from superheavy_survival_audit.schemas import NuclideRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    SourcePointer,
    require_non_empty,
)


def _require_iso_date(value: str, field_name: str) -> str:
    """Validate an ISO-8601 calendar date string."""
    cleaned = require_non_empty(value, field_name)
    try:
        date.fromisoformat(cleaned)
    except ValueError as exc:
        raise SchemaValidationError(
            f"{field_name} must be an ISO-8601 date in YYYY-MM-DD format."
        ) from exc
    return cleaned


def build_upstream_source_key(source_pointer: SourcePointer) -> str:
    """
    Build a stable upstream source key from a source pointer.

    This gives processed snapshots an explicit linkage field that remains easy
    to compare across exports and downstream tables.
    """
    return f"{source_pointer.source_name}:{source_pointer.source_record_id}"


@dataclass(frozen=True, slots=True)
class ProcessedNuclideSnapshot:
    """
    Release-grade processed nuclide export record.

    This record is derived from the canonical NuclideRecord and carries forward
    core uncertainty metadata in a flat, comparison-friendly form.
    """

    snapshot_id: str
    repository_version: str
    generated_date: str
    nuclide_id: str
    element_symbol: str
    atomic_number_z: int
    neutron_number_n: int
    mass_number_a: int
    isomer_label: str
    is_evaluated: bool
    source_key: str
    source_name: str
    source_record_id: str
    half_life_seconds: float | None = None
    half_life_uncertainty_seconds: float | None = None
    has_half_life_value: bool = False
    has_half_life_uncertainty: bool = False
    half_life_relative_uncertainty: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_id",
            require_non_empty(self.snapshot_id, "snapshot_id"),
        )
        object.__setattr__(
            self,
            "repository_version",
            require_non_empty(self.repository_version, "repository_version"),
        )
        object.__setattr__(
            self,
            "generated_date",
            _require_iso_date(self.generated_date, "generated_date"),
        )
        object.__setattr__(
            self,
            "nuclide_id",
            require_non_empty(self.nuclide_id, "nuclide_id"),
        )
        object.__setattr__(
            self,
            "element_symbol",
            require_non_empty(self.element_symbol, "element_symbol"),
        )
        object.__setattr__(
            self,
            "isomer_label",
            require_non_empty(self.isomer_label, "isomer_label"),
        )
        object.__setattr__(
            self,
            "source_key",
            require_non_empty(self.source_key, "source_key"),
        )
        object.__setattr__(
            self,
            "source_name",
            require_non_empty(self.source_name, "source_name"),
        )
        object.__setattr__(
            self,
            "source_record_id",
            require_non_empty(self.source_record_id, "source_record_id"),
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

        if self.half_life_seconds is not None and self.half_life_seconds < 0:
            raise SchemaValidationError("half_life_seconds must be non-negative.")

        if (
            self.half_life_uncertainty_seconds is not None
            and self.half_life_uncertainty_seconds < 0
        ):
            raise SchemaValidationError(
                "half_life_uncertainty_seconds must be non-negative."
            )

        if self.has_half_life_value != (self.half_life_seconds is not None):
            raise SchemaValidationError(
                "has_half_life_value must match whether half_life_seconds is present."
            )

        if self.has_half_life_uncertainty != (
            self.half_life_uncertainty_seconds is not None
        ):
            raise SchemaValidationError(
                "has_half_life_uncertainty must match whether "
                "half_life_uncertainty_seconds is present."
            )

        if self.half_life_relative_uncertainty is not None:
            if self.half_life_seconds is None or self.half_life_seconds == 0:
                raise SchemaValidationError(
                    "half_life_relative_uncertainty requires a non-zero half-life value."
                )
            if self.half_life_relative_uncertainty < 0:
                raise SchemaValidationError(
                    "half_life_relative_uncertainty must be non-negative."
                )

    @classmethod
    def from_nuclide_record(
        cls,
        record: NuclideRecord,
        *,
        snapshot_id: str,
        repository_version: str,
        generated_date: str,
    ) -> "ProcessedNuclideSnapshot":
        """Build a processed export record from a canonical NuclideRecord."""
        relative_uncertainty: float | None = None
        if (
            record.half_life_seconds is not None
            and record.half_life_seconds > 0
            and record.half_life_uncertainty_seconds is not None
        ):
            relative_uncertainty = (
                record.half_life_uncertainty_seconds / record.half_life_seconds
            )

        return cls(
            snapshot_id=snapshot_id,
            repository_version=repository_version,
            generated_date=generated_date,
            nuclide_id=record.nuclide_id,
            element_symbol=record.element_symbol,
            atomic_number_z=record.atomic_number_z,
            neutron_number_n=record.neutron_number_n,
            mass_number_a=record.mass_number_a,
            isomer_label=record.isomer_label,
            is_evaluated=record.is_evaluated,
            source_key=build_upstream_source_key(record.source_pointer),
            source_name=record.source_pointer.source_name,
            source_record_id=record.source_pointer.source_record_id,
            half_life_seconds=record.half_life_seconds,
            half_life_uncertainty_seconds=record.half_life_uncertainty_seconds,
            has_half_life_value=(record.half_life_seconds is not None),
            has_half_life_uncertainty=(
                record.half_life_uncertainty_seconds is not None
            ),
            half_life_relative_uncertainty=relative_uncertainty,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)
