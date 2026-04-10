from __future__ import annotations

import json
from pathlib import Path

import pytest

from superheavy_survival_audit.processed import (
    ProcessedNuclideSnapshot,
    build_upstream_source_key,
    export_nuclide_snapshots,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError, SourcePointer
from superheavy_survival_audit.validation import load_nuclide_records


def test_build_upstream_source_key_is_stable_and_explicit() -> None:
    source_pointer = SourcePointer(
        source_name="nubase2020",
        source_record_id="Mc290",
    )

    key = build_upstream_source_key(source_pointer)

    assert key == "nubase2020:Mc290"


def test_processed_snapshot_derives_uncertainty_fields_from_nuclide_record() -> None:
    records = load_nuclide_records(Path("tests/fixtures/nuclides.valid.json"))

    snapshot = ProcessedNuclideSnapshot.from_nuclide_record(
        records[0],
        snapshot_id="snapshot-001",
        repository_version="0.1.0a0",
        generated_date="2026-04-10",
    )

    assert snapshot.nuclide_id == "Mc-290"
    assert snapshot.source_key == "nubase2020:Mc290"
    assert snapshot.has_half_life_value is True
    assert snapshot.has_half_life_uncertainty is True
    assert snapshot.half_life_relative_uncertainty == pytest.approx(0.05 / 0.65)


def test_processed_snapshot_rejects_mismatched_uncertainty_flags() -> None:
    with pytest.raises(SchemaValidationError):
        ProcessedNuclideSnapshot(
            snapshot_id="snapshot-002",
            repository_version="0.1.0a0",
            generated_date="2026-04-10",
            nuclide_id="Mc-290",
            element_symbol="Mc",
            atomic_number_z=115,
            neutron_number_n=175,
            mass_number_a=290,
            isomer_label="ground",
            is_evaluated=True,
            source_key="nubase2020:Mc290",
            source_name="nubase2020",
            source_record_id="Mc290",
            half_life_seconds=0.65,
            half_life_uncertainty_seconds=None,
            has_half_life_value=True,
            has_half_life_uncertainty=True,
            half_life_relative_uncertainty=None,
        )


def test_export_nuclide_snapshots_writes_json_snapshot_file(tmp_path: Path) -> None:
    records = load_nuclide_records(Path("tests/fixtures/nuclides.valid.json"))
    output_path = tmp_path / "nuclide_snapshot.json"

    snapshots = export_nuclide_snapshots(
        records,
        snapshot_id="snapshot-003",
        repository_version="0.1.0a0",
        generated_date="2026-04-10",
        output_path=output_path,
    )

    assert len(snapshots) == 2
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload[0]["snapshot_id"] == "snapshot-003"
    assert payload[0]["source_key"] == "nubase2020:Mc290"
    assert payload[0]["has_half_life_uncertainty"] is True
