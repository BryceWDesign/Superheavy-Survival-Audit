from __future__ import annotations

from pathlib import Path

import pytest

from superheavy_survival_audit.schemas.common import SchemaValidationError
from superheavy_survival_audit.validation import (
    load_benchmark_records,
    load_decay_records,
    load_nuclide_records,
    load_route_records,
)


def test_load_nuclide_records_parses_valid_fixture() -> None:
    records = load_nuclide_records(Path("tests/fixtures/nuclides.valid.json"))

    assert len(records) == 2
    assert records[0].nuclide_id == "Mc-290"
    assert records[0].source_pointer.source_name == "nubase2020"


def test_load_decay_records_parses_valid_fixture() -> None:
    records = load_decay_records(Path("tests/fixtures/decays.valid.json"))

    assert len(records) == 1
    assert records[0].decay_mode == "alpha"
    assert records[0].daughter_nuclide_id == "Nh-286"


def test_load_route_records_parses_valid_fixture() -> None:
    records = load_route_records(Path("tests/fixtures/routes.valid.json"))

    assert len(records) == 1
    assert records[0].feasibility_class == "low"
    assert records[0].bottleneck_penalty == pytest.approx(0.75)


def test_load_benchmark_records_parses_valid_fixture() -> None:
    records = load_benchmark_records(Path("tests/fixtures/benchmarks.valid.json"))

    assert len(records) == 1
    assert records[0].benchmark_kind == "evaluated_data_alignment"


def test_loader_rejects_invalid_canonical_record() -> None:
    with pytest.raises(SchemaValidationError):
        load_nuclide_records(Path("tests/fixtures/nuclides.invalid.json"))


def test_loader_rejects_missing_file() -> None:
    with pytest.raises(SchemaValidationError):
        load_decay_records(Path("tests/fixtures/does_not_exist.json"))
