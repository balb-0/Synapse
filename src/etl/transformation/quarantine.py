"""Quarentena durável por referência; valores brutos permanecem na origem."""

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from .identity import canonical_json, digest
from .validation import Violation


@dataclass(frozen=True)
class RejectedRecord:
    source: str
    source_checksum: str
    source_offset: int
    run_id: str
    batch_id: str
    ingested_at: str
    violations: tuple[Violation, ...]

    @property
    def rejection_id(self):
        return digest([self.source, self.source_checksum, self.source_offset,
                       [(v.code, v.field) for v in self.violations]])


class QuarantineStore:
    """Ledger local de ocorrências, sem payload, e-mail ou chave pessoal.

    O arquivo bruto imutável identificado por checksum deve permanecer no
    armazenamento restrito da extração. Apagar essa origem perde a capacidade
    de reprocessamento: retenção é um contrato do operador, não um TTL implícito.
    """
    def __init__(self, path):
        self.path = Path(path)
        if self.path.is_symlink():
            raise ValueError("UNSAFE_QUARANTINE_PATH")
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if not self.path.is_file() or self.path.stat().st_mode & 0o077:
                raise ValueError("UNSAFE_QUARANTINE_PERMISSIONS") from None
        else:
            os.close(fd)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS rejections (
                rejection_id TEXT NOT NULL, run_id TEXT NOT NULL,
                batch_id TEXT NOT NULL, metadata TEXT NOT NULL,
                PRIMARY KEY (rejection_id, run_id, batch_id))""")

    def persist(self, records):
        with sqlite3.connect(self.path) as db:
            for record in records:
                metadata = {"source": record.source,
                            "source_checksum": record.source_checksum,
                            "source_offset": record.source_offset,
                            "ingested_at": record.ingested_at,
                            "violations": [{"code": v.code, "field": v.field}
                                           for v in record.violations]}
                db.execute("INSERT OR IGNORE INTO rejections VALUES (?, ?, ?, ?)",
                           (record.rejection_id, record.run_id, record.batch_id,
                            canonical_json(metadata)))

    def count(self):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT count(*) FROM rejections").fetchone()[0]
