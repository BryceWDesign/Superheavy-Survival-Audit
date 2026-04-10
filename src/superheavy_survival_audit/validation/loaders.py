"""
JSON import loaders for canonical repository records.

These loaders are intentionally strict. They are used to validate that imported
JSON payloads can be parsed into canonical record objects before later
normalization or downstream processing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, TypeVar

from superheavy_survival_audit.schemas import (
    BenchmarkRecord,
    DecayRecord,
    NuclideRecord,
    RouteRecord,
)
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    SourcePointer,
)

T = TypeVar("T")


def _read_json_array(json_path: str | Path) -> list[dict[str, Any]]:
    """Read a top-level JSON array of objects."""
    path = Path(json_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"JSON file is not valid JSON: {path}") from exc

    if not isinstance(payload, list):
        raise SchemaValidationError(
            f"Canonical import file must contain a top-level JSON array: {path}"
        )

    normalized: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise SchemaValidationError(
                f"Each record in a canonical import file must be a JSON object: {path}"
            )
        normalized.append(item)
    return normalized


def _coerce_source_pointer(record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a source_pointer dictionary into a SourcePointer object.

    This keeps the on-disk JSON friendly while preserving strict schema parsing
    in memory.
    """
    normalized = dict(record)
    if "source_pointer" in normalized:
        pointer = normalized["source_pointer"]
        if not isinstance(pointer, dict):
            raise SchemaValidationError(
                "source_pointer must be a JSON object when provided."
            )
        normalized["source_pointer"] = SourcePointer(**pointer)
    return normalized


def _load_records(
    json_path: str | Path,
    record_factory: Callable[..., T],
) -> list[T]:
    """Generic canonical-record loader from a JSON array."""
    raw_records = _read_json_array(json_path)
    parsed: list[T] = []
    for record in raw_records:
        normalized_record = _coerce_source_pointer(record)
        parsed.append(record_factory(**normalized_record))
    return parsed


def load_nuclide_records(json_path: str | Path) -> list[NuclideRecord]:
    """Load canonical nuclide records from a JSON array file."""
    return _load_records(json_path, NuclideRecord)


def load_decay_records(json_path: str | Path) -> list[DecayRecord]:
    """Load canonical decay records from a JSON array file."""
    return _load_records(json_path, DecayRecord)


def load_route_records(json_path: str | Path) -> list[RouteRecord]:
    """Load canonical route records from a JSON array file."""
    return _load_records(json_path, RouteRecord)


def load_benchmark_records(json_path: str | Path) -> list[BenchmarkRecord]:
    """Load canonical benchmark records from a JSON array file."""
    return _load_records(json_path, BenchmarkRecord)
