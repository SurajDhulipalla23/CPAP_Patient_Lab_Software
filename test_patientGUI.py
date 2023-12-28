import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from DB_init import SleepLabRooms as db
from patientGUI import safe_int_conversion


@pytest.mark.parametrize("test_input, expected", [
    ("123", 123),  # Normal case
    ("-123", -123),  # Negative number
    ("0", 0),  # Zero
    ("9999999999999", 9999999999999),  # Large number
    ("abc", None),  # Non-numeric string
    ("123abc", None),  # Mixed alphanumeric
    ("", None),  # Empty string
    ("12.34", None),  # Decimal number
    ("   123   ", 123),  # String with spaces
    ("+123", 123),  # String with plus sign
])
def test_safe_int_conversion(test_input, expected):
    assert safe_int_conversion(test_input) == expected


@pytest.mark.parametrize("count, expected_output", [
    (0, "black\n"),  # Normal case, black color
    (1, "black\n"),  # Normal case, black color
    (2, "red\n"),    # Boundary case, red color
    (3, "red\n"),    # Normal case, red color
    (-1, "black\n"),  # Negative count, black color
])
def test_apnea_count_color(capsys, count, expected_output):
    from patientGUI import apnea_count_color
    apnea_count_color(count)
    captured = capsys.readouterr()
    assert captured.out == expected_output
