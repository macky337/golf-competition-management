import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from data_integrity import RESTORE_TABLES, fetch_all_rows, validate_backup


def test_restore_rejects_missing_tables_and_empty_payload():
    for payload in ({}, {"scores": []}, {table: [] for table in RESTORE_TABLES}):
        with pytest.raises(ValueError):
            validate_backup(payload)
    valid = {table: [] for table in RESTORE_TABLES}
    valid["players"] = [{"id": 1}]
    validate_backup(valid)
    valid["scores"] = [None]
    with pytest.raises(ValueError):
        validate_backup(valid)


class PagedClient:
    def __init__(self, truncate=False):
        self.rows = [{"id": i} for i in range(1205)]
        self.truncate = truncate

    def table(self, name):
        return self

    def select(self, *args, **kwargs):
        return self

    def order(self, key):
        return self

    def range(self, start, end):
        self.start, self.end = start, end
        return self

    def execute(self):
        page = self.rows[self.start:self.end + 1]
        if self.truncate and self.start >= 500:
            page = []
        return SimpleNamespace(data=page, count=len(self.rows))


def test_backup_reads_all_pages_and_rejects_incomplete_reads():
    assert len(fetch_all_rows(PagedClient(), "scores")) == 1205
    with pytest.raises(ValueError):
        fetch_all_rows(PagedClient(truncate=True), "scores")
