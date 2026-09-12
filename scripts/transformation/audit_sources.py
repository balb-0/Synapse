#!/usr/bin/env python3
"""Auditoria black box de transformação. Não grava registros nem carrega banco."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from etl.extraction.contracts import BatchMetadata, ExtractedBatch, ExtractionCheckpoint
from etl.transformation.consistency import ReferenceData
from etl.transformation.pipeline import transform_batch


def audit(directory, source_timezone=None):
    references, report = {}, {}
    for source in ("empresas", "pesquisas", "clientes", "respondentes", "questoes", "respostas"):
        path = directory / (source + ".csv")
        if source == "respostas" and not path.exists():
            path = directory / "teste.csv"
        content = path.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, delimiter=";", strict=True)
            headers = next(reader)
            # Repeated anonymous export columns must not overwrite each other.
            headers = [h if h.strip() else f"Unnamed: {i}" for i, h in enumerate(headers)]
            if len(set(headers)) != len(headers):
                raise ValueError("DUPLICATE_CSV_HEADER")
            rows = []
            for values in reader:
                if len(values) != len(headers):
                    raise ValueError("INVALID_CSV_WIDTH")
                rows.append(dict(zip(headers, values)))
        now = datetime.now(timezone.utc)
        batch = ExtractedBatch(
            rows,
            ExtractionCheckpoint(source, "audit-only", 0),
            BatchMetadata(
                source,
                "audit",
                "transformation",
                source,
                now,
                now,
                len(rows),
                len(content),
                "1.0",
                checksum,
            ),
        )
        result = transform_batch(
            batch,
            references=ReferenceData(references),
            previous={},
            source_offset=0,
            ingested_at=now,
            source_timezone=source_timezone,
        )
        issues = Counter(v.code for record in result.rejected for v in record.violations)
        report[source] = {
            k: v for k, v in result.metrics.items() if k.endswith("_count") or k == "input_bytes"
        }
        report[source].update(
            source_checksum=checksum, rejection_codes=dict(sorted(issues.items()))
        )
        if source != "respondentes":
            references[source] = [record.data for record in result.accepted]
    return {
        "mode": "transformation-only-no-load",
        "source_timezone": source_timezone,
        "sources": report,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--source-timezone")
    args = parser.parse_args()
    try:
        report = audit(args.source_dir, args.source_timezone)
    except (OSError, ValueError, csv.Error):
        parser.exit(
            1, "AUDIT_FAILED: verificar arquivos, schema e configuração; valores omitidos.\n"
        )
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
