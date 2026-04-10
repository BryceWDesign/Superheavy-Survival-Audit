"""
Canonical provenance data structures.

These models are intentionally strict. Every transformed record in the
repository should eventually be able to explain:

- which upstream source it came from
- what version or release identity was associated with that source
- when it was accessed
- what transformation steps were applied
- which repository version produced the transformed record
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Tuple

from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
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


@dataclass(frozen=True, slots=True)
class SourceRegistryEntry:
    """
    Canonical source-registry entry.

    This describes an upstream source known to the repository, not a specific
    imported record. Per-record linkage will be stored elsewhere.
    """

    source_id: str
    display_name: str
    publisher: str
    access_mode: str
    homepage_url: str
    citation_hint: str
    license_note: str
    version_hint: str | None = None
    last_verified_date: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", require_non_empty(self.source_id, "source_id"))
        object.__setattr__(
            self,
            "display_name",
            require_non_empty(self.display_name, "display_name"),
        )
        object.__setattr__(self, "publisher", require_non_empty(self.publisher, "publisher"))
        object.__setattr__(
            self,
            "access_mode",
            require_non_empty(self.access_mode, "access_mode"),
        )
        object.__setattr__(
            self,
            "homepage_url",
            require_non_empty(self.homepage_url, "homepage_url"),
        )
        object.__setattr__(
            self,
            "citation_hint",
            require_non_empty(self.citation_hint, "citation_hint"),
        )
        object.__setattr__(
            self,
            "license_note",
            require_non_empty(self.license_note, "license_note"),
        )

        if self.version_hint is not None:
            object.__setattr__(
                self,
                "version_hint",
                require_non_empty(self.version_hint, "version_hint"),
            )

        if self.last_verified_date is not None:
            object.__setattr__(
                self,
                "last_verified_date",
                _require_iso_date(self.last_verified_date, "last_verified_date"),
            )


@dataclass(frozen=True, slots=True)
class TransformationStep:
    """
    One explicit transformation step applied between raw source material and a
    repository-managed output.
    """

    step_id: str
    operation: str
    input_artifact: str
    output_artifact: str
    rationale: str
    code_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_id", require_non_empty(self.step_id, "step_id"))
        object.__setattr__(
            self,
            "operation",
            require_non_empty(self.operation, "operation"),
        )
        object.__setattr__(
            self,
            "input_artifact",
            require_non_empty(self.input_artifact, "input_artifact"),
        )
        object.__setattr__(
            self,
            "output_artifact",
            require_non_empty(self.output_artifact, "output_artifact"),
        )
        object.__setattr__(
            self,
            "rationale",
            require_non_empty(self.rationale, "rationale"),
        )

        if self.code_reference is not None:
            object.__setattr__(
                self,
                "code_reference",
                require_non_empty(self.code_reference, "code_reference"),
            )


@dataclass(frozen=True, slots=True)
class RecordProvenance:
    """
    Provenance attached to a repository-managed record or artifact.

    This object binds an upstream source to the repository transformation chain.
    """

    provenance_id: str
    source_id: str
    source_record_id: str
    repository_version: str
    access_date: str
    raw_artifact_path: str
    processed_artifact_path: str
    transformation_steps: Tuple[TransformationStep, ...] = field(default_factory=tuple)
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provenance_id",
            require_non_empty(self.provenance_id, "provenance_id"),
        )
        object.__setattr__(self, "source_id", require_non_empty(self.source_id, "source_id"))
        object.__setattr__(
            self,
            "source_record_id",
            require_non_empty(self.source_record_id, "source_record_id"),
        )
        object.__setattr__(
            self,
            "repository_version",
            require_non_empty(self.repository_version, "repository_version"),
        )
        object.__setattr__(
            self,
            "access_date",
            _require_iso_date(self.access_date, "access_date"),
        )
        object.__setattr__(
            self,
            "raw_artifact_path",
            require_non_empty(self.raw_artifact_path, "raw_artifact_path"),
        )
        object.__setattr__(
            self,
            "processed_artifact_path",
            require_non_empty(self.processed_artifact_path, "processed_artifact_path"),
        )

        normalized_steps = tuple(self.transformation_steps)
        for step in normalized_steps:
            if not isinstance(step, TransformationStep):
                raise SchemaValidationError(
                    "transformation_steps must contain only TransformationStep objects."
                )
        object.__setattr__(self, "transformation_steps", normalized_steps)

        if self.notes is not None:
            object.__setattr__(self, "notes", require_non_empty(self.notes, "notes"))
