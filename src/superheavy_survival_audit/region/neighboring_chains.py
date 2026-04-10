"""
Neighboring-chain expansion utilities.

This module defines the initial target-region window for the repository:
Nh, Fl, Mc, Lv, Ts, and Og.

The goal here is modest and deliberate. We are not making a physics claim.
We are creating a clean, validated way to filter canonical nuclide records into
the intended superheavy comparison region and summarize neighboring chains
around a chosen anchor element.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from superheavy_survival_audit.schemas import NuclideRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
)

SUPERHEAVY_REGION_SYMBOLS: tuple[str, ...] = ("Nh", "Fl", "Mc", "Lv", "Ts", "Og")

_EXPECTED_ATOMIC_NUMBERS: dict[str, int] = {
    "Nh": 113,
    "Fl": 114,
    "Mc": 115,
    "Lv": 116,
    "Ts": 117,
    "Og": 118,
}


def _normalize_allowed_symbols(
    allowed_symbols: Iterable[str] | None,
) -> tuple[str, ...]:
    """Validate and normalize an allowed symbol sequence."""
    if allowed_symbols is None:
        return SUPERHEAVY_REGION_SYMBOLS

    normalized: list[str] = []
    for symbol in allowed_symbols:
        cleaned = require_non_empty(symbol, "allowed_symbol")
        if cleaned not in _EXPECTED_ATOMIC_NUMBERS:
            raise SchemaValidationError(
                f"Unsupported superheavy region symbol: {cleaned}"
            )
        if cleaned not in normalized:
            normalized.append(cleaned)

    if not normalized:
        raise SchemaValidationError("allowed_symbols must not be empty.")
    return tuple(normalized)


def _sort_key(record: NuclideRecord) -> tuple[int, int, str]:
    """Return the deterministic sort key for target-region nuclide records."""
    return (record.atomic_number_z, record.mass_number_a, record.isomer_label)


def filter_superheavy_region_records(
    records: Iterable[NuclideRecord],
    *,
    allowed_symbols: Iterable[str] | None = None,
) -> list[NuclideRecord]:
    """
    Filter canonical nuclide records to the supported superheavy comparison region.

    Records are returned in deterministic order by Z, then A, then isomer label.
    """
    allowed = _normalize_allowed_symbols(allowed_symbols)

    filtered: list[NuclideRecord] = []
    for record in records:
        if record.element_symbol not in allowed:
            continue

        expected_z = _EXPECTED_ATOMIC_NUMBERS[record.element_symbol]
        if record.atomic_number_z != expected_z:
            raise SchemaValidationError(
                "NuclideRecord atomic_number_z does not match the expected "
                f"value for {record.element_symbol}."
            )
        filtered.append(record)

    return sorted(filtered, key=_sort_key)


def build_neighboring_chain_window(
    anchor_symbol: str,
    *,
    flank: int = 2,
) -> tuple[str, ...]:
    """
    Build a neighboring element window around an anchor symbol.

    Example:
    - anchor_symbol='Mc', flank=2 -> ('Nh', 'Fl', 'Mc', 'Lv', 'Ts')
    - anchor_symbol='Og', flank=2 -> ('Lv', 'Ts', 'Og')
    """
    cleaned_anchor = require_non_empty(anchor_symbol, "anchor_symbol")
    if cleaned_anchor not in SUPERHEAVY_REGION_SYMBOLS:
        raise SchemaValidationError(
            f"anchor_symbol must be one of: {', '.join(SUPERHEAVY_REGION_SYMBOLS)}"
        )

    if flank < 0:
        raise SchemaValidationError("flank must be zero or greater.")

    ordered = list(SUPERHEAVY_REGION_SYMBOLS)
    anchor_index = ordered.index(cleaned_anchor)
    start_index = max(0, anchor_index - flank)
    end_index = min(len(ordered), anchor_index + flank + 1)
    return tuple(ordered[start_index:end_index])


@dataclass(frozen=True, slots=True)
class NeighboringChainSummary:
    """
    Summary of one element chain within the superheavy comparison region.
    """

    element_symbol: str
    atomic_number_z: int
    nuclide_ids: tuple[str, ...]
    mass_numbers: tuple[int, ...]
    neutron_numbers: tuple[int, ...]
    is_anchor: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "element_symbol",
            require_non_empty(self.element_symbol, "element_symbol"),
        )

        if self.element_symbol not in _EXPECTED_ATOMIC_NUMBERS:
            raise SchemaValidationError(
                f"Unsupported element_symbol for neighboring chain: {self.element_symbol}"
            )

        expected_z = _EXPECTED_ATOMIC_NUMBERS[self.element_symbol]
        if int(self.atomic_number_z) != expected_z:
            raise SchemaValidationError(
                "atomic_number_z does not match the expected target-region value "
                f"for {self.element_symbol}."
            )
        object.__setattr__(self, "atomic_number_z", expected_z)

        nuclide_ids = tuple(self.nuclide_ids)
        mass_numbers = tuple(int(value) for value in self.mass_numbers)
        neutron_numbers = tuple(int(value) for value in self.neutron_numbers)

        if not nuclide_ids:
            raise SchemaValidationError("nuclide_ids must not be empty.")
        if len(nuclide_ids) != len(mass_numbers) or len(nuclide_ids) != len(
            neutron_numbers
        ):
            raise SchemaValidationError(
                "nuclide_ids, mass_numbers, and neutron_numbers must have matching lengths."
            )

        object.__setattr__(self, "nuclide_ids", nuclide_ids)
        object.__setattr__(self, "mass_numbers", mass_numbers)
        object.__setattr__(self, "neutron_numbers", neutron_numbers)

    @property
    def count(self) -> int:
        """Return the number of nuclide records summarized in the chain."""
        return len(self.nuclide_ids)


def summarize_neighboring_chains(
    records: Iterable[NuclideRecord],
    *,
    anchor_symbol: str = "Mc",
    flank: int = 2,
) -> list[NeighboringChainSummary]:
    """
    Summarize neighboring element chains around an anchor element.

    The returned summaries are restricted to the validated neighboring window
    around the anchor symbol and sorted in increasing atomic number.
    """
    window = build_neighboring_chain_window(anchor_symbol, flank=flank)
    filtered = filter_superheavy_region_records(records, allowed_symbols=window)

    grouped: dict[str, list[NuclideRecord]] = {symbol: [] for symbol in window}
    for record in filtered:
        grouped[record.element_symbol].append(record)

    summaries: list[NeighboringChainSummary] = []
    for symbol in window:
        chain_records = sorted(grouped[symbol], key=_sort_key)
        if not chain_records:
            continue

        summaries.append(
            NeighboringChainSummary(
                element_symbol=symbol,
                atomic_number_z=_EXPECTED_ATOMIC_NUMBERS[symbol],
                nuclide_ids=tuple(record.nuclide_id for record in chain_records),
                mass_numbers=tuple(record.mass_number_a for record in chain_records),
                neutron_numbers=tuple(record.neutron_number_n for record in chain_records),
                is_anchor=(symbol == anchor_symbol),
            )
        )

    return summaries
