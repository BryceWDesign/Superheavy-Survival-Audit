from __future__ import annotations

import pytest

from superheavy_survival_audit.schemas import (
    BenchmarkRecord,
    DecayRecord,
    NuclideRecord,
    RouteRecord,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError, SourcePointer


def test_nuclide_record_accepts_valid_values() -> None:
    record = NuclideRecord(
        nuclide_id="Mc-290",
        element_symbol="Mc",
        atomic_number_z=115,
        neutron_number_n=175,
        mass_number_a=290,
        half_life_seconds=0.65,
        half_life_uncertainty_seconds=0.05,
        source_pointer=SourcePointer(
            source_name="nubase",
            source_record_id="Mc290",
        ),
    )

    assert record.atomic_number_z == 115
    assert record.neutron_number_n == 175
    assert record.mass_number_a == 290
    assert record.half_life_seconds == pytest.approx(0.65)


def test_nuclide_record_rejects_inconsistent_mass_number() -> None:
    with pytest.raises(SchemaValidationError):
        NuclideRecord(
            nuclide_id="bad",
            element_symbol="Mc",
            atomic_number_z=115,
            neutron_number_n=175,
            mass_number_a=291,
        )


def test_decay_record_accepts_known_mode_and_branching() -> None:
    record = DecayRecord(
        decay_id="Mc-290-alpha",
        parent_nuclide_id="Mc-290",
        daughter_nuclide_id="Nh-286",
        decay_mode="alpha",
        branching_fraction=0.82,
        branching_uncertainty=0.03,
        q_value_mev=10.12,
        q_value_uncertainty_mev=0.11,
    )

    assert record.decay_mode == "alpha"
    assert record.branching_fraction == pytest.approx(0.82)


def test_decay_record_rejects_invalid_mode() -> None:
    with pytest.raises(SchemaValidationError):
        DecayRecord(
            decay_id="bad-mode",
            parent_nuclide_id="Mc-290",
            decay_mode="magic",
        )


def test_route_record_accepts_non_operational_feasibility_metadata() -> None:
    record = RouteRecord(
        route_id="route-001",
        target_nuclide_id="Mc-290",
        route_class="fusion_evaporation",
        descriptor="Candidate heavy-ion route abstraction",
        feasibility_class="low",
        bottleneck_penalty=0.75,
    )

    assert record.route_class == "fusion_evaporation"
    assert record.bottleneck_penalty == pytest.approx(0.75)


def test_route_record_rejects_penalty_above_one() -> None:
    with pytest.raises(SchemaValidationError):
        RouteRecord(
            route_id="route-002",
            target_nuclide_id="Mc-290",
            route_class="fusion_evaporation",
            descriptor="Too large penalty",
            bottleneck_penalty=1.2,
        )


def test_benchmark_record_accepts_expected_fields() -> None:
    record = BenchmarkRecord(
        benchmark_id="bench-001",
        subject_id="Mc-290",
        benchmark_kind="evaluated_data_alignment",
        reference_label="NUBASE comparison",
        status="informational",
    )

    assert record.reference_label == "NUBASE comparison"
    assert record.status == "informational"


def test_benchmark_record_rejects_unknown_status() -> None:
    with pytest.raises(SchemaValidationError):
        BenchmarkRecord(
            benchmark_id="bench-002",
            subject_id="Mc-290",
            benchmark_kind="literature_expectation",
            reference_label="paper-x",
            status="excellent",
        )
