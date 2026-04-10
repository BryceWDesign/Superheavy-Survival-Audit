"""
Processed snapshot export utilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from superheavy_survival_audit.schemas import NuclideRecord

from .nuclide_snapshot import ProcessedNuclideSnapshot


def export_nuclide_snapshots(
    records: Iterable[NuclideRecord],
    *,
    snapshot_id: str,
    repository_version: str,
    generated_date: str,
    output_path: str | Path,
) -> list[ProcessedNuclideSnapshot]:
    """
    Export canonical nuclide records into a flat processed snapshot JSON file.

    The file written to disk is a JSON array of processed snapshot records.
    """
    snapshots = [
        ProcessedNuclideSnapshot.from_nuclide_record(
            record,
            snapshot_id=snapshot_id,
            repository_version=repository_version,
            generated_date=generated_date,
        )
        for record in records
    ]

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [snapshot.to_dict() for snapshot in snapshots]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return snapshots
