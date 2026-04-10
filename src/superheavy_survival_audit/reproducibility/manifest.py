"""
Reproducibility manifest model.

This model captures the minimum structured metadata needed to tie a generated
artifact set to repository state, source-registry context, and generation paths.
"""

from __future__ import annotations

from dataclasses import dataclass
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


def _require_non_empty_path_list(
    values: tuple[str, ...] | list[str],
    field_name: str,
) -> tuple[str, ...]:
    """Validate a non-empty tuple of non-empty repository paths."""
    normalized = tuple(values)
    if not normalized:
        raise SchemaValidationError(f"{field_name} must contain at least one path.")
    cleaned_values: list[str] = []
    for item in normalized:
        cleaned_values.append(require_non_empty(item, field_name))
    return tuple(cleaned_values)


@dataclass(frozen=True, slots=True)
class ReproducibilityManifest:
    """
    Snapshot-level reproducibility envelope for repository-generated artifacts.
    """

    manifest_id: str
    manifest_version: str
    repository_name: str
    repository_version: str
    generated_date: str
    source_registry_path: str
    input_artifacts: Tuple[str, ...]
    output_artifacts: Tuple[str, ...]
    code_paths: Tuple[str, ...]
    source_registry_hash: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manifest_id",
            require_non_empty(self.manifest_id, "manifest_id"),
        )
        object.__setattr__(
            self,
            "manifest_version",
            require_non_empty(self.manifest_version, "manifest_version"),
        )
        object.__setattr__(
            self,
            "repository_name",
            require_non_empty(self.repository_name, "repository_name"),
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
            "source_registry_path",
            require_non_empty(self.source_registry_path, "source_registry_path"),
        )
        object.__setattr__(
            self,
            "input_artifacts",
            _require_non_empty_path_list(
                self.input_artifacts,
                "input_artifacts",
            ),
        )
        object.__setattr__(
            self,
            "output_artifacts",
            _require_non_empty_path_list(
                self.output_artifacts,
                "output_artifacts",
            ),
        )
        object.__setattr__(
            self,
            "code_paths",
            _require_non_empty_path_list(
                self.code_paths,
                "code_paths",
            ),
        )

        if self.source_registry_hash is not None:
            object.__setattr__(
                self,
                "source_registry_hash",
                require_non_empty(self.source_registry_hash, "source_registry_hash"),
            )

        if self.notes is not None:
            object.__setattr__(self, "notes", require_non_empty(self.notes, "notes"))
