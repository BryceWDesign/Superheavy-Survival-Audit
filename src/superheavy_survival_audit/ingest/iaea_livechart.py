"""
IAEA LiveChart ingestion adapter.

This module provides a conservative adapter for turning CSV-style LiveChart
exports into canonical repository records. It intentionally avoids network I/O
so the repository can validate and normalize downloaded upstream data in a
repeatable way.

The adapter is alias-based rather than tightly coupled to one exact upstream
column layout. That keeps the parsing layer resilient when equivalent fields
appear under slightly different names across exports.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

from superheavy_survival_audit.schemas import DecayRecord, NuclideRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError, SourcePointer


_LIVECHART_BASE_URL = "https://www-nds.iaea.org/relnsd/v1/data"


def build_livechart_query_url(**query_params: str | int | float) -> str:
    """
    Build a LiveChart query URL from explicit query parameters.

    This helper does not fetch data. It only constructs a deterministic URL
    string suitable for logging, provenance notes, or manual retrieval.
    """
    normalized_params: dict[str, str] = {}
    for key, value in query_params.items():
        normalized_params[str(key)] = str(value)
    return f"{_LIVECHART_BASE_URL}?{urlencode(normalized_params)}"


def _read_text(path: str | Path) -> str:
    """Read UTF-8 text from a filesystem path."""
    return Path(path).read_text(encoding="utf-8")


def _parse_csv_text(csv_text: str) -> list[dict[str, str]]:
    """Parse CSV text into a list of stripped dictionaries."""
    stream = io.StringIO(csv_text)
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        raise SchemaValidationError("LiveChart CSV payload is missing a header row.")

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
    """Return the first non-empty field found among the aliases."""
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


def _optional_branching_fraction(
    row: dict[str, str],
    aliases: Iterable[str],
) -> float | None:
    """
    Return an optional branching fraction as a probability in [0, 1].

    If the upstream value is greater than 1, this function assumes the source
    is providing percent units and converts by dividing by 100.
    """
    value = _optional_float(row, aliases)
    if value is None:
        return None
    if value > 1.0:
        value = value / 100.0
    return value


def _normalize_isomer_label(row: dict[str, str]) -> str:
    """Return a conservative isomer label from common alias fields."""
    raw_label = _first_present(
        row,
        (
            "isomer_label",
            "isomer",
            "state",
            "energy_level_label",
        ),
    )
    if raw_label is None:
        return "ground"

    lowered = raw_label.strip().lower()
    if lowered in {"", "g", "gs", "ground", "ground_state"}:
        return "ground"
    return lowered


class IAEALiveChartAdapter:
    """
    Conservative CSV adapter for IAEA LiveChart exports.

    The adapter offers explicit parse methods for canonical nuclide and decay
    records. Each parsed record receives an embedded source pointer suitable for
    early-stage provenance linkage.
    """

    source_name = "iaea_livechart"

    def load_csv_rows(self, csv_path: str | Path) -> list[dict[str, str]]:
        """Load and parse a LiveChart CSV export from disk."""
        return _parse_csv_text(_read_text(csv_path))

    def parse_nuclide_rows(self, rows: list[dict[str, str]]) -> list[NuclideRecord]:
        """Convert CSV rows into canonical nuclide records."""
        parsed: list[NuclideRecord] = []
        for row in rows:
            z_value = int(_require_field(row, ("z", "Z", "atomic_number_z"), "z"))
            n_value = int(_require_field(row, ("n", "N", "neutron_number_n"), "n"))
            a_value = int(_require_field(row, ("a", "A", "mass_number_a"), "a"))
            symbol = _require_field(
                row,
                ("symbol", "element_symbol", "elem_symbol"),
                "element_symbol",
            )

            nuclide_id = _first_present(
                row,
                ("nuclide_id", "nuclide", "nuclide_name"),
            )
            if nuclide_id is None:
                nuclide_id = f"{symbol}-{a_value}"

            half_life_seconds = _optional_float(
                row,
                (
                    "half_life_sec",
                    "half_life_seconds",
                    "half_life_s",
                ),
            )
            half_life_uncertainty_seconds = _optional_float(
                row,
                (
                    "half_life_uncertainty_sec",
                    "half_life_uncertainty_seconds",
                    "half_life_unc_s",
                ),
            )

            source_record_id = _first_present(
                row,
                (
                    "record_id",
                    "source_record_id",
                    "nuclide_id",
                    "nuclide",
                ),
            )
            if source_record_id is None:
                source_record_id = nuclide_id

            parsed.append(
                NuclideRecord(
                    nuclide_id=nuclide_id,
                    element_symbol=symbol,
                    atomic_number_z=z_value,
                    neutron_number_n=n_value,
                    mass_number_a=a_value,
                    isomer_label=_normalize_isomer_label(row),
                    half_life_seconds=half_life_seconds,
                    half_life_uncertainty_seconds=half_life_uncertainty_seconds,
                    is_evaluated=True,
                    source_pointer=SourcePointer(
                        source_name=self.source_name,
                        source_record_id=source_record_id,
                    ),
                )
            )
        return parsed

    def parse_decay_rows(self, rows: list[dict[str, str]]) -> list[DecayRecord]:
        """Convert CSV rows into canonical decay records."""
        parsed: list[DecayRecord] = []
        for row in rows:
            parent_symbol = _require_field(
                row,
                ("parent_symbol", "symbol", "element_symbol"),
                "parent_symbol",
            )
            parent_a = int(
                _require_field(
                    row,
                    ("parent_a", "a_parent", "mass_number_a"),
                    "parent_a",
                )
            )
            parent_id = _first_present(
                row,
                ("parent_nuclide_id", "parent_nuclide", "parent"),
            )
            if parent_id is None:
                parent_id = f"{parent_symbol}-{parent_a}"

            daughter_symbol = _first_present(
                row,
                ("daughter_symbol", "d_symbol", "daughter_element_symbol"),
            )
            daughter_a_text = _first_present(
                row,
                ("daughter_a", "a_daughter", "daughter_mass_number_a"),
            )
            daughter_id: str | None = None
            if daughter_symbol is not None and daughter_a_text is not None:
                daughter_id = _first_present(
                    row,
                    ("daughter_nuclide_id", "daughter_nuclide", "daughter"),
                )
                if daughter_id is None:
                    daughter_id = f"{daughter_symbol}-{int(daughter_a_text)}"

            source_record_id = _first_present(
                row,
                (
                    "record_id",
                    "source_record_id",
                    "decay_id",
                ),
            )
            decay_id = _first_present(row, ("decay_id",))
            if decay_id is None:
                mode = _require_field(
                    row,
                    ("decay_mode", "mode", "decay"),
                    "decay_mode",
                )
                decay_id = f"{parent_id}-{mode}"

            if source_record_id is None:
                source_record_id = decay_id

            parsed.append(
                DecayRecord(
                    decay_id=decay_id,
                    parent_nuclide_id=parent_id,
                    decay_mode=_require_field(
                        row,
                        ("decay_mode", "mode", "decay"),
                        "decay_mode",
                    ),
                    daughter_nuclide_id=daughter_id,
                    branching_fraction=_optional_branching_fraction(
                        row,
                        (
                            "branching_fraction",
                            "branching_ratio",
                            "branching_percent",
                        ),
                    ),
                    branching_uncertainty=_optional_branching_fraction(
                        row,
                        (
                            "branching_uncertainty",
                            "branching_uncertainty_percent",
                        ),
                    ),
                    q_value_mev=_optional_float(
                        row,
                        ("q_value_mev", "q_mev", "q_value"),
                    ),
                    q_value_uncertainty_mev=_optional_float(
                        row,
                        (
                            "q_value_uncertainty_mev",
                            "q_unc_mev",
                            "q_value_uncertainty",
                        ),
                    ),
                    source_pointer=SourcePointer(
                        source_name=self.source_name,
                        source_record_id=source_record_id,
                    ),
                )
            )
        return parsed

    def load_nuclide_records(self, csv_path: str | Path) -> list[NuclideRecord]:
        """Load canonical nuclide records directly from a CSV file."""
        return self.parse_nuclide_rows(self.load_csv_rows(csv_path))

    def load_decay_records(self, csv_path: str | Path) -> list[DecayRecord]:
        """Load canonical decay records directly from a CSV file."""
        return self.parse_decay_rows(self.load_csv_rows(csv_path))
