"""
Shared schema helpers and validation utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class SchemaValidationError(ValueError):
    """Raised when a schema record fails validation."""


def require_non_empty(value: str, field_name: str) -> str:
    """Return a stripped non-empty string or raise a validation error."""
    cleaned = value.strip()
    if not cleaned:
        raise SchemaValidationError(f"{field_name} must be a non-empty string.")
    return cleaned


def require_non_negative(value: float | int, field_name: str) -> float:
    """Return a non-negative float or raise a validation error."""
    numeric = float(value)
    if numeric < 0:
        raise SchemaValidationError(f"{field_name} must be non-negative.")
    return numeric


def require_probability(value: float | int, field_name: str) -> float:
    """Return a probability in [0, 1] or raise a validation error."""
    numeric = float(value)
    if numeric < 0 or numeric > 1:
        raise SchemaValidationError(f"{field_name} must be between 0 and 1.")
    return numeric


def require_membership(value: str, field_name: str, allowed: Iterable[str]) -> str:
    """Return a value when it matches the allowed set or raise."""
    cleaned = value.strip()
    allowed_set = tuple(allowed)
    if cleaned not in allowed_set:
        allowed_text = ", ".join(allowed_set)
        raise SchemaValidationError(
            f"{field_name} must be one of: {allowed_text}."
        )
    return cleaned


@dataclass(frozen=True, slots=True)
class SourcePointer:
    """
    Minimal upstream source pointer stored directly on canonical records.

    More detailed provenance structures will be added later, but every record
    should already be able to point back to a named upstream source and a
    source-specific identifier.
    """

    source_name: str
    source_record_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_name", require_non_empty(self.source_name, "source_name")
        )
        object.__setattr__(
            self,
            "source_record_id",
            require_non_empty(self.source_record_id, "source_record_id"),
        )
