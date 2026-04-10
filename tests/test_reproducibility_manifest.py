from __future__ import annotations

import pytest

from superheavy_survival_audit.reproducibility import ReproducibilityManifest
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_reproducibility_manifest_accepts_valid_payload() -> None:
    manifest = ReproducibilityManifest(
        manifest_id="manifest-001",
        manifest_version="1.0.0",
        repository_name="Superheavy-Survival-Audit",
        repository_version="0.1.0a0",
        generated_date="2026-04-10",
        source_registry_path="data/registry/source_registry.json",
        input_artifacts=(
            "data/raw/example/input.json",
            "data/registry/source_registry.json",
        ),
        output_artifacts=(
            "data/processed/example/output.json",
            "results/example/benchmark_pack.json",
        ),
        code_paths=(
            "src/superheavy_survival_audit/provenance/registry.py",
            "src/superheavy_survival_audit/reproducibility/manifest.py",
        ),
        source_registry_hash="sha256:example",
        notes="Initial manifest test.",
    )

    assert manifest.repository_name == "Superheavy-Survival-Audit"
    assert len(manifest.input_artifacts) == 2
    assert manifest.generated_date == "2026-04-10"


def test_reproducibility_manifest_requires_non_empty_input_artifacts() -> None:
    with pytest.raises(SchemaValidationError):
        ReproducibilityManifest(
            manifest_id="manifest-002",
            manifest_version="1.0.0",
            repository_name="Superheavy-Survival-Audit",
            repository_version="0.1.0a0",
            generated_date="2026-04-10",
            source_registry_path="data/registry/source_registry.json",
            input_artifacts=(),
            output_artifacts=("data/processed/example/output.json",),
            code_paths=("src/superheavy_survival_audit/reproducibility/manifest.py",),
        )


def test_reproducibility_manifest_rejects_bad_date() -> None:
    with pytest.raises(SchemaValidationError):
        ReproducibilityManifest(
            manifest_id="manifest-003",
            manifest_version="1.0.0",
            repository_name="Superheavy-Survival-Audit",
            repository_version="0.1.0a0",
            generated_date="04-10-2026",
            source_registry_path="data/registry/source_registry.json",
            input_artifacts=("data/raw/example/input.json",),
            output_artifacts=("data/processed/example/output.json",),
            code_paths=("src/superheavy_survival_audit/reproducibility/manifest.py",),
        )


def test_reproducibility_manifest_rejects_blank_code_path_entries() -> None:
    with pytest.raises(SchemaValidationError):
        ReproducibilityManifest(
            manifest_id="manifest-004",
            manifest_version="1.0.0",
            repository_name="Superheavy-Survival-Audit",
            repository_version="0.1.0a0",
            generated_date="2026-04-10",
            source_registry_path="data/registry/source_registry.json",
            input_artifacts=("data/raw/example/input.json",),
            output_artifacts=("data/processed/example/output.json",),
            code_paths=("   ",),
        )
