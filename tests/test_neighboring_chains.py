from __future__ import annotations

from pathlib import Path

import pytest

from superheavy_survival_audit.region import (
    SUPERHEAVY_REGION_SYMBOLS,
    build_neighboring_chain_window,
    filter_superheavy_region_records,
    summarize_neighboring_chains,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError
from superheavy_survival_audit.validation import load_nuclide_records


def test_superheavy_region_symbols_are_locked_in_expected_order() -> None:
    assert SUPERHEAVY_REGION_SYMBOLS == ("Nh", "Fl", "Mc", "Lv", "Ts", "Og")


def test_filter_superheavy_region_records_excludes_outside_elements() -> None:
    records = load_nuclide_records(Path("tests/fixtures/superheavy_region.seed.json"))

    filtered = filter_superheavy_region_records(records)

    assert len(filtered) == 8
    assert all(record.element_symbol in SUPERHEAVY_REGION_SYMBOLS for record in filtered)
    assert filtered[0].nuclide_id == "Nh-286"
    assert filtered[-1].nuclide_id == "Og-295"


def test_build_neighboring_chain_window_for_mc_with_flank_two() -> None:
    window = build_neighboring_chain_window("Mc", flank=2)

    assert window == ("Nh", "Fl", "Mc", "Lv", "Ts")


def test_build_neighboring_chain_window_rejects_unknown_anchor() -> None:
    with pytest.raises(SchemaValidationError):
        build_neighboring_chain_window("Xe", flank=2)


def test_summarize_neighboring_chains_groups_by_element_around_mc() -> None:
    records = load_nuclide_records(Path("tests/fixtures/superheavy_region.seed.json"))

    summaries = summarize_neighboring_chains(records, anchor_symbol="Mc", flank=2)

    assert [summary.element_symbol for summary in summaries] == [
        "Nh",
        "Fl",
        "Mc",
        "Lv",
        "Ts",
    ]
    assert summaries[1].nuclide_ids == ("Fl-288", "Fl-289")
    assert summaries[2].is_anchor is True
    assert summaries[2].count == 2


def test_summarize_neighboring_chains_trims_window_at_upper_edge() -> None:
    records = load_nuclide_records(Path("tests/fixtures/superheavy_region.seed.json"))

    summaries = summarize_neighboring_chains(records, anchor_symbol="Og", flank=2)

    assert [summary.element_symbol for summary in summaries] == ["Lv", "Ts", "Og"]
    assert summaries[-1].is_anchor is True
