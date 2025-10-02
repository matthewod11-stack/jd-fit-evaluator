from ui.constants import TABLE_COLUMNS, EXPORT_COLUMNS


def test_export_alignment():
    assert EXPORT_COLUMNS is TABLE_COLUMNS
    assert list(EXPORT_COLUMNS) == list(TABLE_COLUMNS)
