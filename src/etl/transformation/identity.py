"""Identidade e comparação puras; persistência pertence ao consumidor de carga."""

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal

from .schema import KEYS, SCHEMA_VERSION


def json_value(value):
    if isinstance(value, Decimal):
        # Equivalent numeric values must hash equally (1, 1.0 and 1.000).
        return "0" if value == 0 else format(value.normalize(), "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    return value


def canonical_json(value):
    return json.dumps(
        json_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def record_identity(source, record, source_checksum, source_offset):
    if source in KEYS:
        key = [record[k] for k in KEYS[source]]
    else:
        # Participation has no confirmed natural event ID. Physical occurrence
        # preserves identical legitimate events; redelivery of that occurrence
        # has the same identity even when run_id and batch boundaries change.
        key = [source_checksum, source_offset]
    return digest([SCHEMA_VERSION, source, key])


def classify_duplicates(items, previous):
    """Return outcomes without reserving keys before the load is durable.

    Each item is (identity, content_checksum). ``previous`` is the confirmed
    snapshot identity -> checksum. The loader must serialize/atomically check
    this state: this pure function does not claim concurrent exactly-once load.
    """
    versions = {}
    for key, checksum in items:
        versions.setdefault(key, set()).add(checksum)
    seen, outcomes = set(), []
    for key, checksum in items:
        if len(versions[key]) > 1 or (key in previous and previous[key] != checksum):
            outcomes.append("conflict")
        elif key in previous or key in seen:
            outcomes.append("duplicate")
        else:
            outcomes.append("accepted")
        seen.add(key)
    return outcomes
