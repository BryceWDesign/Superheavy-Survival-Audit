"""
Source registry loading utilities.
"""

from __future__ import annotations

import json
from pathlib import Path

from superheavy_survival_audit.schemas.common import SchemaValidationError

from .models import SourceRegistryEntry


def load_source_registry(registry_path: str | Path) -> list[SourceRegistryEntry]:
    """
    Load a source registry from a JSON file.

    The registry file must contain a top-level JSON array of objects.
    """
    path = Path(registry_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"Registry file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(
            f"Registry file is not valid JSON: {path}"
        ) from exc

    if not isinstance(payload, list):
        raise SchemaValidationError(
            "Source registry must be a top-level JSON array of objects."
        )

    entries: list[SourceRegistryEntry] = []
    for item in payload:
        if not isinstance(item, dict):
            raise SchemaValidationError(
                "Each source registry entry must be a JSON object."
            )
        entries.append(SourceRegistryEntry(**item))
    return entries


def registry_index_by_id(
    entries: list[SourceRegistryEntry],
) -> dict[str, SourceRegistryEntry]:
    """
    Index source registry entries by source_id.

    Raises a SchemaValidationError on duplicate source_id values.
    """
    index: dict[str, SourceRegistryEntry] = {}
    for entry in entries:
        if entry.source_id in index:
            raise SchemaValidationError(
                f"Duplicate source_id in registry: {entry.source_id}"
            )
        index[entry.source_id] = entry
    return index
