import pytest
from datetime import datetime, timedelta
from DB_init import SleepLabRooms as db
from unittest.mock import MagicMock, patch
from server import validate_room_number

t1 = datetime(2023, 11, 30, 20, 0, 0)


@pytest.fixture
def mock_db():
    with patch('server.db') as mock:
        yield mock


@pytest.fixture
def mock_validate_room_number():
    with patch('server.validate_room_number') as mock:
        yield mock


@pytest.mark.parametrize("room_number, valid_room, patient_data, expected", [
    (101, True, {"cpap_pressure": 20}, (20, 200)),  # Valid room with data
    (102, False, None, (False, 400)),  # Invalid room
])
def test_fetch_pressure_driver(
    mock_db, mock_validate_room_number, room_number,
    valid_room, patient_data, expected
):
    from server import fetch_pressure_driver
    # Setup the mocks
    mock_validate_room_number.return_value = valid_room
    if valid_room:
        mock_patient = MagicMock()
        mock_patient.cpap_pressure = patient_data['cpap_pressure']
        mock_db.objects.raw({"_id": room_number}
                            ).first.return_value = mock_patient
    else:
        mock_db.objects.raw({"_id": room_number}).first.return_value = None

    # Call the function
    result = fetch_pressure_driver(room_number)

    # Assert the expected result
    assert result == expected


@pytest.mark.parametrize(
    "in_data, expected_response",
    [
        (
            {
                "patient_mrn": "1234",
                "patient_name": "John Doe",
                "cpap_pressure": "20",
                "cpap_calculations": "calc1",
                "room_number": "101"
            },
            ("Patient Info updated successfully.", 200)
        ),
    ]
)
def test_upload_patient_function(mock_db, in_data, expected_response):
    from server import upload_patient_function
    # Mock existing or new patient
    mock_db.objects.get.side_effect = [MagicMock(), db.DoesNotExist()]

    response = upload_patient_function(in_data)

    assert response == expected_response


@pytest.mark.parametrize("input, expected", [
    (t1, "2023-11-30 20:00:00"),
    ("2023-11-30 20:00:00",
     "Invalid argument, must be valid datetime.datetime object")
])
def test_format_date(input, expected):
    from server import format_date
    assert format_date(input) == expected


@pytest.mark.parametrize("input, expected", [
    (123, (True, 123)),
    ("123", (True, 123)),
    ("a123", (False, "Value cannot be converted to integer.")),
    ("123a", (False, "Value cannot be converted to integer.")),
    ("", (False, "Value cannot be converted to integer."))
])
def test_validate_and_convert_int(input, expected):
    from server import validate_and_convert_int
    assert validate_and_convert_int(input) == expected


mock_result1 = {"patient_mrn": "1",
                "test_name": "LDL",
                "test_result": 110}
mock_result2 = {"patient_mrn": 2,
                "test_name": "HDL",
                "test_result": 65}
mock_result3 = {"patient_mrn": 3,
                "test_name": "LDL",
                "test_result": 110}
mock_result4 = {"patient_mrn": 1,
                "test_name": "TSH",
                "test_result": 1.5}
mock_result5 = {"patient_mrn": "1",
                "test_name": "ldl",
                "test_result": 130.0}
mock_result6 = {"mrn": "1",
                "test_name": "LDL",
                "test_result": 130}
mock_result7 = {"patient_mrn": 1,
                "test_name": "LDL",
                "test_result": "130"}


@pytest.mark.parametrize("data, keys, types, expected", [
    (mock_result1, ["patient_mrn", "test_name", "test_result"],
     [[int, str], [str], [int, float]], True),
    (mock_result6, ["patient_mrn", "test_name", "test_result"],
     [[int, str], [str], [int, float]],
     "patient_mrn key is not found in the input"),
    (mock_result7, ["patient_mrn", "test_name", "test_result"],
     [[int, str], [str], [int, float]],
     "test_result key should be of type <class 'int'> or <class 'float'>."),
])
def test_input_verification(data, keys, types, expected):
    from server import input_verification
    assert input_verification(data, keys, types) == expected


def test_list_rooms_driver():
    from server import list_rooms_driver
    assert list_rooms_driver() == ([1, 2, 3, 4], 200)


mock_update1 = {"room_number": 4, "cpap_pressure": 3}
mock_update2 = {"room_number": 4, "cpap_pressure": 10}
mock_update3 = {"room_number": 4, "cpap_pressure": "10"}
mock_update4 = {"room_number": 5, "cpap_pressure": 10}
mock_update5 = {"room_number": 4, "cpap_pressure": 14}


def test_lab_update_cpap_pressure_driver():
    from server import lab_update_cpap_pressure_driver as func
    msg1 = "Pressure must be an integer between 4 and 25, inclusive."
    msg2 = "CPAP pressure successfully updated."
    msg3 = "Patient not associated with room number entry."
    msg4 = "cpap_pressure key should be of type <class 'int'>."
    assert func(mock_update1) == (msg1, 400)
    assert func(mock_update2) == (msg2, 200)
    updated = db.objects.raw({"_id": mock_update2["room_number"]}).first()
    assert updated.cpap_pressure == mock_update2["cpap_pressure"]
    assert func(mock_update3) == (msg4, 400)
    assert func(mock_update4) == (msg3, 400)
    assert func(mock_update5) == (msg2, 200)
    updated = db.objects.raw({"_id": mock_update5["room_number"]}).first()
    assert updated.cpap_pressure == mock_update5["cpap_pressure"]


@pytest.mark.parametrize("input, expected", [
    ("10", "Pressure must be an integer between 4 and 25, inclusive."),
    (10, True),
    (25, True),
    (26, "Pressure must be an integer between 4 and 25, inclusive."),
    ("26", "Pressure must be an integer between 4 and 25, inclusive."),
])
def test_cpap_pressure_validation(input, expected):
    from server import cpap_pressure_validation
    assert cpap_pressure_validation(input) == expected


@pytest.mark.parametrize("input, expected", [
    (2, True),
    (3, True),
    ("3", "Patient not associated with room number entry."),
    (5, "Patient not associated with room number entry."),
])
def test_validate_room_number(input, expected):
    from server import validate_room_number
    assert validate_room_number(input) == expected


def test_fetch_patient_driver():
    from server import fetch_patient_driver
    patient_dict, status_code, result = fetch_patient_driver(4)
    assert (
        db.objects.raw(
            {"patient_name": result.patient_name}).first().room_number == 4)
    assert patient_dict["room_number"] == 4
    assert status_code == 200
    result, status_code, patient = fetch_patient_driver(5)
    assert result == "Patient not associated with room number entry."
    assert status_code == 400
    assert patient is None


def test_file_to_b64_string():
    # Adapted from David Ward, Duke University
    from server import file_to_b64_string
    b64str = file_to_b64_string("test_data/test_image.jpg")
    assert b64str[0:20] == "/9j/4AAQSkZJRgABAQEA"


def test_b64_string_to_file():
    # Adapted from David Ward, Duke University
    from server import file_to_b64_string
    from server import b64_string_to_file
    import filecmp
    import os
    b64str = file_to_b64_string("test_data/test_image.jpg")
    b64_string_to_file(b64str, "test_data/test_image_output.jpg")
    answer = filecmp.cmp("test_data/test_image.jpg",
                         "test_data/test_image_output.jpg")
    os.remove("test_data/test_image_output.jpg")
    assert answer


patient_dict1 = {"room_number": 1,
                 "patient_name": "John Doe",
                 "patient_mrn": 100,
                 "cpap_pressure": 15,
                 "cpap_calculations": [
                     ["2023-11-29T10:00:00", 18, 2, "image1.png"],
                     ["2023-11-29T12:00:00", 17, 3, "image2.png"]]}


def test_SleepLabRooms_to_dict():
    from server import SleepLabRooms_to_dict as func
    patient1 = db.objects.raw({"_id": 1}).first()
    msg1 = "Input must be SleepLabRooms instance."
    assert func(patient1) == (True, patient_dict1)
    assert func(patient_dict1) == (False, msg1)
