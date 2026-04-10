from __future__ import annotations

from pathlib import Path

import pytest

from superheavy_survival_audit.ingest import (
    IAEALiveChartAdapter,
    build_livechart_query_url,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_build_livechart_query_url_includes_query_parameters() -> None:
    url = build_livechart_query_url(fields="ground_states", nuclides="Mc-290")

    assert url.startswith("https://www-nds.iaea.org/relnsd/v1/data?")
    assert "fields=ground_states" in url
    assert "nuclides=Mc-290" in url


def test_livechart_adapter_loads_nuclide_records_from_csv() -> None:
    adapter = IAEALiveChartAdapter()

    records = adapter.load_nuclide_records(
        Path("tests/fixtures/iaea_livechart_nuclides.sample.csv")
    )

    assert len(records) == 2
    assert records[0].nuclide_id == "Mc-290"
    assert records[0].source_pointer.source_name == "iaea_livechart"
    assert records[0].half_life_seconds == pytest.approx(0.65)


def test_livechart_adapter_loads_decay_records_from_csv() -> None:
    adapter = IAEALiveChartAdapter()

    records = adapter.load_decay_records(
        Path("tests/fixtures/iaea_livechart_decays.sample.csv")
    )

    assert len(records) == 2
    assert records[0].decay_mode == "alpha"
    assert records[0].branching_fraction == pytest.approx(0.82)
    assert records[1].decay_mode == "spontaneous_fission"
    assert records[1].daughter_nuclide_id is None


def test_livechart_adapter_rejects_missing_required_nuclide_field() -> None:
    adapter = IAEALiveChartAdapter()
    bad_rows = [
        {
            "record_id": "bad-row",
            "z": "115",
            "n": "175",
            "symbol": "Mc",
        }
    ]

    with pytest.raises(SchemaValidationError):
        adapter.parse_nuclide_rows(bad_rows)


def test_livechart_adapter_rejects_invalid_csv_without_header() -> None:
    adapter = IAEALiveChartAdapter()
    bad_csv_path = Path("tests/fixtures/iaea_livechart_invalid.sample.csv")

    with pytest.raises(SchemaValidationError):
        adapter.load_nuclide_records(bad_csv_path)
