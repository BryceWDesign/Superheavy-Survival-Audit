"""
ENSDF parsing and normalization layer.

This module intentionally avoids trying to parse raw ENSDF text format directly.
Instead, it normalizes a structured JSON export shape that can be produced from
ENSDF-derived workflows, manual curation, or downstream tooling.

The goal is not to recreate the full ENSDF ecosystem here. The goal is to make
sure the repository can accept structured ENSDF-adjacent decay and radiation
information in a way that preserves provenance and stays compatible with the
canonical repository schemas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from superheavy_survival_audit.schemas import DecayRecord
from superheavy_survival_audit.schemas.common import (
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

_ALLOWED_RADIATION_KINDS = (
    "gamma",
    "xray",
    "alpha",
    "beta",
    "conversion_electron",
    "auger",
    "unknown",
)


def _read_json(path: str | Path) -> dict[str, object]:
    """Read and validate a JSON object from disk."""
    file_path = Path(path)
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"ENSDF JSON file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(
            f"ENSDF JSON file is not valid JSON: {file_path}"
        ) from exc

    if not isinstance(payload, dict):
        raise SchemaValidationError("ENSDF JSON payload must be a top-level object.")
    return payload


def _require_object_list(value: object, field_name: str) -> list[dict[str, object]]:
    """Validate that a field is a list of objects."""
    if not isinstance(value, list):
        raise SchemaValidationError(f"{field_name} must be a list.")
    validated: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise SchemaValidationError(f"{field_name} entries must be objects.")
        validated.append(item)
    return validated


def _optional_float(value: object, field_name: str) -> float | None:
    """Parse an optional numeric value."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned == "":
            return None
        try:
            return float(cleaned)
        except ValueError as exc:
            raise SchemaValidationError(f"{field_name} must be numeric.") from exc
    raise SchemaValidationError(f"{field_name} must be numeric or null.")


@dataclass(frozen=True, slots=True)
class ENSDFDecayBranch:
    """
    Structured ENSDF-derived decay branch.

    This is an ingestion-layer record. It keeps branch-level identity and
    decouples parsing from immediate conversion into the canonical decay schema.
    """

    branch_id: str
    parent_nuclide_id: str
    decay_mode: str
    daughter_nuclide_id: str | None = None
    branching_fraction: float | None = None
    branching_uncertainty: float | None = None
    q_value_mev: float | None = None
    q_value_uncertainty_mev: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_id", require_non_empty(self.branch_id, "branch_id"))
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

    def to_canonical(self) -> DecayRecord:
        """Convert the structured branch into the canonical decay schema."""
        return DecayRecord(
            decay_id=self.branch_id,
            parent_nuclide_id=self.parent_nuclide_id,
            decay_mode=self.decay_mode,
            daughter_nuclide_id=self.daughter_nuclide_id,
            branching_fraction=self.branching_fraction,
            branching_uncertainty=self.branching_uncertainty,
            q_value_mev=self.q_value_mev,
            q_value_uncertainty_mev=self.q_value_uncertainty_mev,
            source_pointer=SourcePointer(
                source_name="ensdf",
                source_record_id=self.branch_id,
            ),
        )


@dataclass(frozen=True, slots=True)
class ENSDFRadiationObservation:
    """
    Structured ENSDF-derived radiation observation.

    This is not yet a canonical repository schema. It exists so the repository
    can retain observability-relevant detail for later modeling without forcing
    that detail into the canonical decay schema prematurely.
    """

    observation_id: str
    parent_nuclide_id: str
    radiation_kind: str
    energy_kev: float | None = None
    intensity_fraction: float | None = None
    intensity_uncertainty: float | None = None
    final_level_label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "observation_id",
            require_non_empty(self.observation_id, "observation_id"),
        )
        object.__setattr__(
            self,
            "parent_nuclide_id",
            require_non_empty(self.parent_nuclide_id, "parent_nuclide_id"),
        )
        object.__setattr__(
            self,
            "radiation_kind",
            require_membership(
                self.radiation_kind,
                "radiation_kind",
                _ALLOWED_RADIATION_KINDS,
            ),
        )

        if self.energy_kev is not None:
            object.__setattr__(
                self,
                "energy_kev",
                require_non_negative(self.energy_kev, "energy_kev"),
            )

        if self.intensity_fraction is not None:
            object.__setattr__(
                self,
                "intensity_fraction",
                require_probability(self.intensity_fraction, "intensity_fraction"),
            )

        if self.intensity_uncertainty is not None:
            object.__setattr__(
                self,
                "intensity_uncertainty",
                require_non_negative(
                    self.intensity_uncertainty,
                    "intensity_uncertainty",
                ),
            )
            if self.intensity_fraction is None:
                raise SchemaValidationError(
                    "intensity_uncertainty requires intensity_fraction."
                )
            if self.intensity_fraction + self.intensity_uncertainty > 1.0 + 1e-12:
                raise SchemaValidationError(
                    "intensity_fraction plus intensity_uncertainty cannot exceed 1."
                )

        if self.final_level_label is not None:
            object.__setattr__(
                self,
                "final_level_label",
                require_non_empty(self.final_level_label, "final_level_label"),
            )


class ENSDFAdapter:
    """
    Structured-export ENSDF adapter.

    Expected JSON shape:

    {
      "dataset_id": "ensdf-example",
      "decay_branches": [ ... ],
      "radiation_observations": [ ... ]
    }
    """

    source_name = "ensdf"

    def load_payload(self, json_path: str | Path) -> dict[str, object]:
        """Load a structured ENSDF JSON payload from disk."""
        return _read_json(json_path)

    def parse_decay_branches(
        self,
        payload: dict[str, object],
    ) -> list[ENSDFDecayBranch]:
        """Parse structured decay branches from a payload."""
        raw_value = payload.get("decay_branches", [])
        raw_branches = _require_object_list(raw_value, "decay_branches")

        parsed: list[ENSDFDecayBranch] = []
        for item in raw_branches:
            parsed.append(
                ENSDFDecayBranch(
                    branch_id=require_non_empty(str(item.get("branch_id", "")), "branch_id"),
                    parent_nuclide_id=require_non_empty(
                        str(item.get("parent_nuclide_id", "")),
                        "parent_nuclide_id",
                    ),
                    decay_mode=str(item.get("decay_mode", "")),
                    daughter_nuclide_id=(
                        None
                        if item.get("daughter_nuclide_id") in (None, "")
                        else str(item["daughter_nuclide_id"])
                    ),
                    branching_fraction=_optional_float(
                        item.get("branching_fraction"),
                        "branching_fraction",
                    ),
                    branching_uncertainty=_optional_float(
                        item.get("branching_uncertainty"),
                        "branching_uncertainty",
                    ),
                    q_value_mev=_optional_float(
                        item.get("q_value_mev"),
                        "q_value_mev",
                    ),
                    q_value_uncertainty_mev=_optional_float(
                        item.get("q_value_uncertainty_mev"),
                        "q_value_uncertainty_mev",
                    ),
                )
            )
        return parsed

    def parse_radiation_observations(
        self,
        payload: dict[str, object],
    ) -> list[ENSDFRadiationObservation]:
        """Parse structured radiation observations from a payload."""
        raw_value = payload.get("radiation_observations", [])
        raw_observations = _require_object_list(
            raw_value,
            "radiation_observations",
        )

        parsed: list[ENSDFRadiationObservation] = []
        for item in raw_observations:
            parsed.append(
                ENSDFRadiationObservation(
                    observation_id=require_non_empty(
                        str(item.get("observation_id", "")),
                        "observation_id",
                    ),
                    parent_nuclide_id=require_non_empty(
                        str(item.get("parent_nuclide_id", "")),
                        "parent_nuclide_id",
                    ),
                    radiation_kind=str(item.get("radiation_kind", "")),
                    energy_kev=_optional_float(item.get("energy_kev"), "energy_kev"),
                    intensity_fraction=_optional_float(
                        item.get("intensity_fraction"),
                        "intensity_fraction",
                    ),
                    intensity_uncertainty=_optional_float(
                        item.get("intensity_uncertainty"),
                        "intensity_uncertainty",
                    ),
                    final_level_label=(
                        None
                        if item.get("final_level_label") in (None, "")
                        else str(item["final_level_label"])
                    ),
                )
            )
        return parsed

    def load_decay_branches(self, json_path: str | Path) -> list[ENSDFDecayBranch]:
        """Load structured ENSDF decay branches from disk."""
        return self.parse_decay_branches(self.load_payload(json_path))

    def load_radiation_observations(
        self,
        json_path: str | Path,
    ) -> list[ENSDFRadiationObservation]:
        """Load structured ENSDF radiation observations from disk."""
        return self.parse_radiation_observations(self.load_payload(json_path))

    def load_canonical_decay_records(self, json_path: str | Path) -> list[DecayRecord]:
        """Load structured ENSDF branches and convert them to canonical decay records."""
        branches = self.load_decay_branches(json_path)
        return [branch.to_canonical() for branch in branches]
