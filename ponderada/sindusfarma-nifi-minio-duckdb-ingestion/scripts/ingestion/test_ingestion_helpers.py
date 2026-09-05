from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from datasets_config import DATASETS, schema_fields
from profile_sources import key_stats, sha256_file


class IngestionHelperTests(unittest.TestCase):
    def test_sha256_file_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.csv"
            path.write_bytes(b"id;value\n1;abc\n")
            expected = "960fdaf616b1d961b8d318b6aa7c143925679da46cb5b6309ea1bdacae49d6e7"
            self.assertEqual(sha256_file(path), expected)
            self.assertEqual(sha256_file(path), expected)

    def test_schema_files_are_valid_json_and_have_fields(self) -> None:
        for dataset in DATASETS:
            fields = schema_fields(dataset)
            self.assertGreater(len(fields), 0, dataset.name)
            self.assertEqual(len(fields), len(set(fields)), dataset.name)

    def test_key_stats_detect_duplicates_and_empty_values(self) -> None:
        rows = [["1", "A"], ["1", "B"], ["", "C"]]
        duplicate_count, empty_count = key_stats(rows, [0])
        self.assertEqual(duplicate_count, 1)
        self.assertEqual(empty_count, 1)

    def test_all_schemas_match_declared_dataset_names(self) -> None:
        for dataset in DATASETS:
            schema = json.loads(
                (Path(__file__).resolve().parents[2] / "nifi" / "schemas" / f"{dataset.name}.avsc").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(schema["name"], dataset.name)


if __name__ == "__main__":
    unittest.main()
