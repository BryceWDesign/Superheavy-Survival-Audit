from __future__ import annotations

import pytest

from superheavy_survival_audit.ingest import AMEMassRecord
from superheavy_survival_audit.modeling import (
    ReferenceMassPrediction,
    build_mass_residual_consensus,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError


def _build_ame_record() -> AMEMassRecord:
    return AMEMassRecord(
        record_id="Mc290",
        element_symbol="Mc",
        atomic_number_z=115,
        neutron_number_n=175,
        mass_number_a=290,
        mass_excess_kev=136512.0,
        mass_excess_uncertainty_kev=215.0,
        atomic_mass_micro_u=290174320.0,
        binding_energy_per_nucleon_kev=7076.4,
    )


def test_build_mass_residual_consensus_scores_close_cluster_higher() -> None:
    observed = _build_ame_record()

    close_cluster = [
        ReferenceMassPrediction(
            model_name="ws4",
            predicted_mass_excess_kev=136500.0,
        ),
        ReferenceMassPrediction(
            model_name="frdm",
            predicted_mass_excess_kev=136540.0,
        ),
        ReferenceMassPrediction(
            model_name="hfb",
            predicted_mass_excess_kev=136490.0,
        ),
    ]
    wide_cluster = [
        ReferenceMassPrediction(
            model_name="ws4",
            predicted_mass_excess_kev=135000.0,
        ),
        ReferenceMassPrediction(
            model_name="frdm",
            predicted_mass_excess_kev=137800.0,
        ),
        ReferenceMassPrediction(
            model_name="hfb",
            predicted_mass_excess_kev=136512.0,
        ),
    ]

    close_summary = build_mass_residual_consensus(observed, close_cluster)
    wide_summary = build_mass_residual_consensus(observed, wide_cluster)

    assert close_summary.model_count == 3
    assert close_summary.mean_absolute_residual_kev < wide_summary.mean_absolute_residual_kev
    assert close_summary.residual_std_kev < wide_summary.residual_std_kev
    assert close_summary.consensus_score > wide_summary.consensus_score


def test_build_mass_residual_consensus_handles_perfect_single_prediction() -> None:
    observed = _build_ame_record()

    summary = build_mass_residual_consensus(
        observed,
        [
            ReferenceMassPrediction(
                model_name="perfect_model",
                predicted_mass_excess_kev=136512.0,
            )
        ],
    )

    assert summary.majority_sign_label == "zero"
    assert summary.sign_agreement_fraction == pytest.approx(1.0)
    assert summary.mean_absolute_residual_kev == pytest.approx(0.0)
    assert summary.residual_std_kev == pytest.approx(0.0)
    assert summary.accuracy_score == pytest.approx(1.0)
    assert summary.spread_score == pytest.approx(1.0)
    assert summary.consensus_score == pytest.approx(1.0)


def test_build_mass_residual_consensus_reports_mixed_signs_when_tied() -> None:
    observed = _build_ame_record()

    summary = build_mass_residual_consensus(
        observed,
        [
            ReferenceMassPrediction(
                model_name="positive_residual_model",
                predicted_mass_excess_kev=136500.0,
            ),
            ReferenceMassPrediction(
                model_name="negative_residual_model",
                predicted_mass_excess_kev=136524.0,
            ),
        ],
    )

    assert summary.majority_sign_label == "mixed"
    assert summary.sign_agreement_fraction == pytest.approx(0.5)


def test_build_mass_residual_consensus_rejects_empty_predictions() -> None:
    observed = _build_ame_record()

    with pytest.raises(SchemaValidationError):
        build_mass_residual_consensus(observed, [])


def test_build_mass_residual_consensus_rejects_duplicate_model_names() -> None:
    observed = _build_ame_record()

    with pytest.raises(SchemaValidationError):
        build_mass_residual_consensus(
            observed,
            [
                ReferenceMassPrediction(
                    model_name="dup_model",
                    predicted_mass_excess_kev=136500.0,
                ),
                ReferenceMassPrediction(
                    model_name="dup_model",
                    predicted_mass_excess_kev=136520.0,
                ),
            ],
        )
