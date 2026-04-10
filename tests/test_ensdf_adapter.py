from __future__ import annotations

from pathlib import Path

import pytest

from superheavy_survival_audit.ingest import ENSDFAdapter
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_ensdf_adapter_loads_structured_decay_branches() -> None:
    adapter = ENSDFAdapter()

    branches = adapter.load_decay_branches(
        Path("tests/fixtures/ensdf_structured.sample.json")
    )

    assert len(branches) == 2
    assert branches[0].branch_id == "Mc290-alpha"
    assert branches[0].decay_mode == "alpha"
    assert branches[1].decay_mode == "spontaneous_fission"


def test_ensdf_adapter_loads_structured_radiation_observations() -> None:
    adapter = ENSDFAdapter()

    observations = adapter.load_radiation_observations(
        Path("tests/fixtures/ensdf_structured.sample.json")
    )

    assert len(observations) == 1
    assert observations[0].radiation_kind == "gamma"
    assert observations[0].energy_kev == pytest.approx(218.5)


def test_ensdf_adapter_converts_branches_to_canonical_decay_records() -> None:
    adapter = ENSDFAdapter()

    records = adapter.load_canonical_decay_records(
        Path("tests/fixtures/ensdf_structured.sample.json")
    )

    assert len(records) == 2
    assert records[0].decay_id == "Mc290-alpha"
    assert records[0].source_pointer.source_name == "ensdf"


def test_ensdf_adapter_rejects_invalid_structured_branch() -> None:
    adapter = ENSDFAdapter()

    with pytest.raises(SchemaValidationError):
        adapter.load_decay_branches(Path("tests/fixtures/ensdf_structured.invalid.json"))


def test_ensdf_adapter_rejects_missing_file() -> None:
    adapter = ENSDFAdapter()

    with pytest.raises(SchemaValidationError):
        adapter.load_payload(Path("tests/fixtures/does_not_exist_ensdf.json"))
