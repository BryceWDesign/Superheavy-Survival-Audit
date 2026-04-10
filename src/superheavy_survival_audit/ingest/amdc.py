"""
AMDC ingestion adapter for AME and NUBASE style tabular exports.

This module is intentionally conservative and file-based. It does not fetch
remote resources. Instead, it parses manually downloaded or archived upstream
tables into typed records suitable for later normalization and joining.

The adapter supports simple delimited text exports with a header row. The
default delimiter is the pipe character so fixture files remain easy to inspect
and robust under manual browser-based repository construction.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from superheavy_survival_audit.schemas import NuclideRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    SourcePointer,
    require_non_empty,
    require_non_negative,
)


def _read_text(path: str | Path) -> str:
    """Read UTF-8 text from disk."""
    return Path(path).read_text(encoding="utf-8")


def _parse_delimited_text(
    table_text: str,
    *,
    delimiter: str = "|",
) -> list[dict[str, str]]:
    """Parse a delimited text payload with a required header row."""
    stream = io.StringIO(table_text)
    reader = csv.DictReader(stream, delimiter=delimiter)
    if reader.fieldnames is None:
        raise SchemaValidationError("AMDC table payload is missing a header row.")

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        normalized_row: dict[str, str] = {}
        for key, value in raw_row.items():
            if key is None:
                continue
            normalized_row[key.strip()] = "" if value is None else value.strip()
        rows.append(normalized_row)
    return rows


def _first_present(row: dict[str, str], aliases: Iterable[str]) -> str | None:
    """Return the first non-empty field found among aliases."""
    for alias in aliases:
        value = row.get(alias)
        if value is not None and value != "":
            return value
    return None


def _require_field(row: dict[str, str], aliases: Iterable[str], label: str) -> str:
    """Return a required field or raise a schema validation error."""
    value = _first_present(row, aliases)
    if value is None:
        alias_text = ", ".join(aliases)
        raise SchemaValidationError(
            f"Missing required field for {label}. Expected one of: {alias_text}."
        )
    return value


def _optional_float(row: dict[str, str], aliases: Iterable[str]) -> float | None:
    """Return an optional float when a matching non-empty field exists."""
    value = _first_present(row, aliases)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise SchemaValidationError(
            f"Expected a numeric field for aliases: {', '.join(aliases)}."
        ) from exc


def _normalize_isomer_label(value: str | None) -> str:
    """Normalize a conservative isomer label."""
    if value is None:
        return "ground"
    lowered = value.strip().lower()
    if lowered in {"", "g", "gs", "ground", "ground_state"}:
        return "ground"
    return lowered


@dataclass(frozen=True, slots=True)
class NUBASENuclideRecord:
    """
    Typed upstream record from a NUBASE-style export.

    This is an ingestion-layer record, not yet a fully normalized processed
    dataset. It preserves the upstream notion of a nuclide-level record and can
    be converted into the repository's canonical NuclideRecord.
    """

    record_id: str
    element_symbol: str
    atomic_number_z: int
    neutron_number_n: int
    mass_number_a: int
    isomer_label: str = "ground"
    half_life_seconds: float | None = None
    half_life_uncertainty_seconds: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", require_non_empty(self.record_id, "record_id"))
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
            self,
            "isomer_label",
            _normalize_isomer_label(self.isomer_label),
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

    @property
    def nuclide_id(self) -> str:
        """Return a canonical nuclide identifier."""
        return f"{self.element_symbol}-{self.mass_number_a}"

    def to_canonical(self) -> NuclideRecord:
        """Convert the upstream NUBASE row into the canonical nuclide schema."""
        return NuclideRecord(
            nuclide_id=self.nuclide_id,
            element_symbol=self.element_symbol,
            atomic_number_z=self.atomic_number_z,
            neutron_number_n=self.neutron_number_n,
            mass_number_a=self.mass_number_a,
            isomer_label=self.isomer_label,
            half_life_seconds=self.half_life_seconds,
            half_life_uncertainty_seconds=self.half_life_uncertainty_seconds,
            is_evaluated=True,
            source_pointer=SourcePointer(
                source_name="nubase2020",
                source_record_id=self.record_id,
            ),
        )


@dataclass(frozen=True, slots=True)
class AMEMassRecord:
    """
    Typed upstream record from an AME-style mass table export.

    This keeps mass-specific information intact before later normalization,
    feature extraction, or benchmark generation.
    """

    record_id: str
    element_symbol: str
    atomic_number_z: int
    neutron_number_n: int
    mass_number_a: int
    mass_excess_kev: float
    mass_excess_uncertainty_kev: float | None = None
    atomic_mass_micro_u: float | None = None
    binding_energy_per_nucleon_kev: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", require_non_empty(self.record_id, "record_id"))
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
        object.__setattr__(self, "mass_excess_kev", float(self.mass_excess_kev))

        if self.mass_excess_uncertainty_kev is not None:
            object.__setattr__(
                self,
                "mass_excess_uncertainty_kev",
                require_non_negative(
                    self.mass_excess_uncertainty_kev,
                    "mass_excess_uncertainty_kev",
                ),
            )

        if self.atomic_mass_micro_u is not None:
            object.__setattr__(
                self,
                "atomic_mass_micro_u",
                require_non_negative(self.atomic_mass_micro_u, "atomic_mass_micro_u"),
            )

        if self.binding_energy_per_nucleon_kev is not None:
            object.__setattr__(
                self,
                "binding_energy_per_nucleon_kev",
                require_non_negative(
                    self.binding_energy_per_nucleon_kev,
                    "binding_energy_per_nucleon_kev",
                ),
            )

    @property
    def nuclide_id(self) -> str:
        """Return a canonical nuclide identifier."""
        return f"{self.element_symbol}-{self.mass_number_a}"

    @property
    def source_pointer(self) -> SourcePointer:
        """Return a conservative source pointer."""
        return SourcePointer(
            source_name="ame2020",
            source_record_id=self.record_id,
        )


class AMDCAdapter:
    """
    Conservative parser for AMDC-style AME and NUBASE tabular exports.
    """

    def load_rows(
        self,
        table_path: str | Path,
        *,
        delimiter: str = "|",
    ) -> list[dict[str, str]]:
        """Load and parse a delimited AMDC export file."""
        return _parse_delimited_text(_read_text(table_path), delimiter=delimiter)

    def parse_nubase_rows(
        self,
        rows: list[dict[str, str]],
    ) -> list[NUBASENuclideRecord]:
        """Convert NUBASE-style rows into typed upstream records."""
        parsed: list[NUBASENuclideRecord] = []
        for row in rows:
            z_value = int(_require_field(row, ("z", "Z", "atomic_number_z"), "z"))
            n_value = int(_require_field(row, ("n", "N", "neutron_number_n"), "n"))
            a_value = int(_require_field(row, ("a", "A", "mass_number_a"), "a"))
            symbol = _require_field(
                row,
                ("symbol", "element_symbol", "elem_symbol"),
                "element_symbol",
            )
            record_id = _require_field(
                row,
                ("record_id", "source_record_id", "nuclide_id"),
                "record_id",
            )

            parsed.append(
                NUBASENuclideRecord(
                    record_id=record_id,
                    element_symbol=symbol,
                    atomic_number_z=z_value,
                    neutron_number_n=n_value,
                    mass_number_a=a_value,
                    isomer_label=_first_present(
                        row,
                        ("isomer_label", "isomer", "state"),
                    )
                    or "ground",
                    half_life_seconds=_optional_float(
                        row,
                        ("half_life_seconds", "half_life_sec", "half_life_s"),
                    ),
                    half_life_uncertainty_seconds=_optional_float(
                        row,
                        (
                            "half_life_uncertainty_seconds",
                            "half_life_uncertainty_sec",
                            "half_life_unc_s",
                        ),
                    ),
                )
            )
        return parsed

    def parse_ame_rows(self, rows: list[dict[str, str]]) -> list[AMEMassRecord]:
        """Convert AME-style rows into typed upstream mass records."""
        parsed: list[AMEMassRecord] = []
        for row in rows:
            z_value = int(_require_field(row, ("z", "Z", "atomic_number_z"), "z"))
            n_value = int(_require_field(row, ("n", "N", "neutron_number_n"), "n"))
            a_value = int(_require_field(row, ("a", "A", "mass_number_a"), "a"))
            symbol = _require_field(
                row,
                ("symbol", "element_symbol", "elem_symbol"),
                "element_symbol",
            )
            record_id = _require_field(
                row,
                ("record_id", "source_record_id", "nuclide_id"),
                "record_id",
            )

            parsed.append(
                AMEMassRecord(
                    record_id=record_id,
                    element_symbol=symbol,
                    atomic_number_z=z_value,
                    neutron_number_n=n_value,
                    mass_number_a=a_value,
                    mass_excess_kev=float(
                        _require_field(
                            row,
                            ("mass_excess_kev", "mass_excess_kev_value"),
                            "mass_excess_kev",
                        )
                    ),
                    mass_excess_uncertainty_kev=_optional_float(
                        row,
                        (
                            "mass_excess_uncertainty_kev",
                            "mass_excess_unc_kev",
                        ),
                    ),
                    atomic_mass_micro_u=_optional_float(
                        row,
                        ("atomic_mass_micro_u", "atomic_mass_u_micro"),
                    ),
                    binding_energy_per_nucleon_kev=_optional_float(
                        row,
                        (
                            "binding_energy_per_nucleon_kev",
                            "be_per_a_kev",
                        ),
                    ),
                )
            )
        return parsed

    def load_nubase_records(
        self,
        table_path: str | Path,
        *,
        delimiter: str = "|",
    ) -> list[NUBASENuclideRecord]:
        """Load typed NUBASE-style records from disk."""
        return self.parse_nubase_rows(self.load_rows(table_path, delimiter=delimiter))

    def load_ame_records(
        self,
        table_path: str | Path,
        *,
        delimiter: str = "|",
    ) -> list[AMEMassRecord]:
        """Load typed AME-style mass records from disk."""
        return self.parse_ame_rows(self.load_rows(table_path, delimiter=delimiter))

    def load_nubase_as_canonical_nuclides(
        self,
        table_path: str | Path,
        *,
        delimiter: str = "|",
    ) -> list[NuclideRecord]:
        """Load NUBASE rows and convert them directly to canonical nuclide records."""
        upstream_records = self.load_nubase_records(table_path, delimiter=delimiter)
        return [record.to_canonical() for record in upstream_records]
