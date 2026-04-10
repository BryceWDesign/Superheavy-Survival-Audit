from __future__ import annotations

from pathlib import Path

import pytest

from superheavy_survival_audit.provenance import (
    RecordProvenance,
    SourceRegistryEntry,
    TransformationStep,
    load_source_registry,
    registry_index_by_id,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_source_registry_entry_accepts_valid_values() -> None:
    entry = SourceRegistryEntry(
        source_id="iaea_livechart",
        display_name="IAEA LiveChart of Nuclides",
        publisher="International Atomic Energy Agency",
        access_mode="api",
        homepage_url="https://example.org/source",
        citation_hint="Cite the upstream source.",
        license_note="Upstream terms apply.",
        version_hint="v0",
        last_verified_date="2026-04-10",
    )

    assert entry.source_id == "iaea_livechart"
    assert entry.last_verified_date == "2026-04-10"


def test_source_registry_entry_rejects_bad_date() -> None:
    with pytest.raises(SchemaValidationError):
        SourceRegistryEntry(
            source_id="bad",
            display_name="Bad Source",
            publisher="Publisher",
            access_mode="api",
            homepage_url="https://example.org/source",
            citation_hint="Cite the upstream source.",
            license_note="Upstream terms apply.",
            last_verified_date="04-10-2026",
        )


def test_transformation_step_requires_non_empty_fields() -> None:
    step = TransformationStep(
        step_id="step-001",
        operation="normalize_units",
        input_artifact="data/raw/source.csv",
        output_artifact="data/processed/source.json",
        rationale="Create a normalized intermediate representation.",
        code_reference="src/module.py:normalize_units",
    )

    assert step.operation == "normalize_units"
    assert step.code_reference == "src/module.py:normalize_units"


def test_record_provenance_accepts_transformation_steps() -> None:
    provenance = RecordProvenance(
        provenance_id="prov-001",
        source_id="iaea_livechart",
        source_record_id="Mc-290",
        repository_version="0.1.0a0",
        access_date="2026-04-10",
        raw_artifact_path="data/raw/iaea_livechart/mc_290.json",
        processed_artifact_path="data/processed/nuclides/mc_290.normalized.json",
        transformation_steps=(
            TransformationStep(
                step_id="step-001",
                operation="normalize_fields",
                input_artifact="data/raw/iaea_livechart/mc_290.json",
                output_artifact="data/processed/nuclides/mc_290.normalized.json",
                rationale="Map upstream keys into canonical repository fields.",
            ),
        ),
        notes="Initial normalization path.",
    )

    assert provenance.source_id == "iaea_livechart"
    assert len(provenance.transformation_steps) == 1


def test_record_provenance_rejects_non_step_items() -> None:
    with pytest.raises(SchemaValidationError):
        RecordProvenance(
            provenance_id="prov-002",
            source_id="iaea_livechart",
            source_record_id="Mc-290",
            repository_version="0.1.0a0",
            access_date="2026-04-10",
            raw_artifact_path="data/raw/x.json",
            processed_artifact_path="data/processed/x.json",
            transformation_steps=("not-a-step",),
        )


def test_load_source_registry_reads_json_entries() -> None:
    registry_path = Path("data/registry/source_registry.json")
    entries = load_source_registry(registry_path)

    assert len(entries) >= 4
    assert entries[0].source_id == "iaea_livechart"


def test_registry_index_by_id_rejects_duplicates() -> None:
    duplicate_entries = [
        SourceRegistryEntry(
            source_id="dup",
            display_name="One",
            publisher="Publisher",
            access_mode="api",
            homepage_url="https://example.org/one",
            citation_hint="Cite one.",
            license_note="Terms apply.",
        ),
        SourceRegistryEntry(
            source_id="dup",
            display_name="Two",
            publisher="Publisher",
            access_mode="api",
            homepage_url="https://example.org/two",
            citation_hint="Cite two.",
            license_note="Terms apply.",
        ),
    ]

    with pytest.raises(SchemaValidationError):
        registry_index_by_id(duplicate_entries)
