from __future__ import annotations

from pathlib import Path

import pytest

from superheavy_survival_audit.ingest import AMDCAdapter
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_amdc_adapter_loads_nubase_records() -> None:
    adapter = AMDCAdapter()

    records = adapter.load_nubase_records(Path("tests/fixtures/nubase2020.sample.psv"))

    assert len(records) == 2
    assert records[0].record_id == "Mc290"
    assert records[0].nuclide_id == "Mc-290"
    assert records[0].half_life_seconds == pytest.approx(0.65)


def test_amdc_adapter_converts_nubase_records_to_canonical_nuclides() -> None:
    adapter = AMDCAdapter()

    records = adapter.load_nubase_as_canonical_nuclides(
        Path("tests/fixtures/nubase2020.sample.psv")
    )

    assert len(records) == 2
    assert records[0].nuclide_id == "Mc-290"
    assert records[0].source_pointer.source_name == "nubase2020"


def test_amdc_adapter_loads_ame_mass_records() -> None:
    adapter = AMDCAdapter()

    records = adapter.load_ame_records(Path("tests/fixtures/ame2020.sample.psv"))

    assert len(records) == 2
    assert records[0].record_id == "Mc290"
    assert records[0].mass_excess_kev == pytest.approx(136512.0)
    assert records[0].source_pointer.source_name == "ame2020"


def test_amdc_adapter_rejects_missing_required_ame_field() -> None:
    adapter = AMDCAdapter()
    bad_rows = [
        {
            "record_id": "Mc290",
            "z": "115",
            "n": "175",
            "a": "290",
            "symbol": "Mc",
        }
    ]

    with pytest.raises(SchemaValidationError):
        adapter.parse_ame_rows(bad_rows)


def test_amdc_adapter_rejects_invalid_nubase_mass_consistency() -> None:
    adapter = AMDCAdapter()
    bad_rows = [
        {
            "record_id": "BadMc",
            "z": "115",
            "n": "175",
            "a": "291",
            "symbol": "Mc",
            "isomer_label": "ground",
        }
    ]

    with pytest.raises(SchemaValidationError):
        adapter.parse_nubase_rows(bad_rows)
