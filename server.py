from flask import Flask, request, jsonify
from pymodm import connect
from pymodm import errors as pymodm_errors
from datetime import datetime, timedelta
from DB_init import SleepLabRooms as db
import base64
import requests

app = Flask(__name__)


def format_date(datetime_obj):
    """Converts datetime objects an appropriately formatted string
    representation.

    Timestamps of posted requests or results are stored in the server
    database. This function converts datetime objects in the datetime module to
    a desired string representation.

    Parameters
    ----------
    datetime_obj : datetime.datetime instance
        The datetime object to be converted to a string representation

    Returns
    -------
    str
        The converted timestamp string.
    """
    try:
        dtstr = datetime.strftime(datetime_obj, "%Y-%m-%d %H:%M:%S")
    except TypeError:
        return "Invalid argument, must be valid datetime.datetime object"
    return dtstr


def validate_and_convert_int(input):
    """Validates and converts an input value to an integer.

    This function checks if the provided input value is a valid number
    or a numeric string. If the input is valid,
    it converts the input to an integer.
    If the input contains any letters or non-numeric characters,
    the input is considered invalid.

    Parameters
    ----------
    input : str or int
        The input value to be validated and possibly converted to an integer.

    Returns
    -------
    bool
        True if the input is a valid number or numeric string, False otherwise.
    int or str
        The converted integer value if the input is valid,
        or an error message if it is invalid.
    """
    try:
        return True, int(input)
    except ValueError:
        return False, "Value cannot be converted to integer."


def input_verification(in_data, expected_keys, expected_types):
    """Validates an input dictionary

    This function receives the input data and a list/tuple of the
    expected keys and expected value types. The expected value types must be
    passed as lists/tuples. If only one expected type is accepted, a list/
    tuple with a single entry must be passed. This function verifies that the
    input data is a dictionary, that it contains the keys founds in the
    expected keys, and that the values for the keys are of the expected type.
    If all checks pass, True is returned.  If any verification fails, an error
    message is returned. The list of expected value types should be in the
    same order as the expected keys.

    Adapted from David Ward, Duke University.

    Parameters
    ----------
    in_data : dict
        The input dictionary
    expected_keys : list/tuple
        a list or tuple of what keys should be in the input dictionary
    expected_types : list/tuple of list/tuple
        a list or tuple of lists/tuples of expected value types for each key,
        in the same order as the expected keys

    Returns
    -------
    bool or string
        True is validation passes, an error message if it fails
    """
    if type(in_data) is not dict:
        return "Data sent must be a dictionary."
    for key in expected_keys:
        if key not in in_data.keys():
            return "{} key is not found in the input".format(key)
    for ex_type, ex_key in zip(expected_types, expected_keys):
        if type(in_data[ex_key]) not in ex_type:
            type_string = format_type_list_string(ex_type)
            return "{} key should be of type {}.".format(ex_key, type_string)
    return True


def format_type_list_string(type_list):
    """Formats string for list of types in input verification

    The input_verifcation function is passed a list of list of accepted types
    for each associated key. When a dictionary is passed with an entry of an
    invalid type, an error message is returned. This function creates a string
    from a list of types that can be readily used in this error message. For
    example, if `[int, str]` is a list of accepted types, the associated
    string is "<class 'int'> or <class 'str'>".

    Parameters
    ----------
    type_list : list of type
        list of types to be formatted

    Returns
    -------
    string
        string representation of each type separated by " or "
    """
    type_string = ""
    for type in type_list:
        type_string += "{} or ".format(type)
    type_string = type_string[:-4]
    return type_string


@app.route('/lab/list_rooms', methods=['GET'])
def list_rooms():
    """Returns list of room numbers in server database.

    This function implements the GET route `/lab/list_rooms`. A driver
    function is called returning a list where each entry is room number
    corresponding to a monitored patient. The list of room numbers is
    returned with a 200 status code.

    Parameters
    ----------
    None

    Returns
    -------
    string
        JSON encoding of list of room numbers
    int
        status code
    """
    rooms, status_code = list_rooms_driver()
    return jsonify(rooms), status_code


def list_rooms_driver():
    """
    Returns list of room numbers in server database.

    This function implements the GET route `/lab/list_rooms`. A QuerySet
    object containing SleepLabRooms objects is called from the database. The
    QuerySet object is iterated over, and each room number is appended to a
    list. The list of room numbers is returned with a 200 status code.

    Parameters
    ----------
    None

    Returns
    -------
    list
        list of room numbers
    int
        status code
    """
    results = db.objects.raw({})
    rooms = []
    for patient in results:
        rooms.append(patient.room_number)
    return rooms, 200


@app.route('/patient/upload_patient', methods=['POST'])
def upload_patient():
    """
    POST route for uploading patient data.

    This function implements the POST route `/patient/upload_patient`. This
    POST request receives a JSON string containing patient data and forwards
    it to the `upload_patient_driver` function. The driver function processes
    the data and returns a confirmation/error message along with a status code.

    The JSON string should contain the following keys:
        - room_number: int, patient room number.
        - patient_name: string, patient name.
        - patient_mrn: int, patient medical record number.
        - cpap_pressure: int, entered cpap pressure number.
        - cpap_calculations: list containing breathing rate,
        number of apnea events and flow rate vs time.

    Parameters
    ----------
    None

    Returns
    -------
    string
        Confirmation or error message.
    int
        HTTP status code.
    """
    in_data = request.get_json()
    result, status_code = upload_patient_driver(in_data)
    return result, status_code


def upload_patient_function(in_data):
    # Rigurously tested using the MongoDB database
    """
    Uploads or updates a patient's data in the database.

    This function takes patient data from `in_data`, including CPAP pressure,
    room number, and CPAP calculations. It attempts to find an existing patient
    record by MRN. If found, the record is updated; if not, a new record is
    created. Returns a message and HTTP status code upon completion.

    Parameters
    ----------
    in_data : dict
        A dictionary containing the patient's data including MRN, name, CPAP
        pressure, and calculations.

    Returns
    -------
    tuple
        A tuple containing a response message and HTTP status code.
    """
    new_pressure = in_data["cpap_pressure"]
    room_number = in_data["room_number"]
    new_cpap_calculations = in_data["cpap_calculations"]
    try:
        existing_patient = db.objects.get(
            {'patient_mrn': in_data["patient_mrn"]})

        # Update the existing record
        existing_patient.patient_name = in_data["patient_name"]
        existing_patient.cpap_pressure = new_pressure
        existing_patient.cpap_calculations.append(new_cpap_calculations)
        existing_patient.save()
        return "Patient Info updated successfully.", 200

    except db.DoesNotExist:
        new_patient = db(room_number=room_number,
                         patient_name=in_data["patient_name"],
                         patient_mrn=in_data["patient_mrn"],
                         cpap_pressure=new_pressure,
                         cpap_calculations=[new_cpap_calculations])
        new_patient.save()

        return "Patient successfully Added.", 200


def upload_patient_driver(in_data):
    # Rigurously tested using the MongoDB database
    # Helper functions also rigorously tested
    """
    Driver function for processing patient data.

    This function takes the input data received from the `upload_patient` POST
    route, verifies the input, and updates the patient data in the database.
    It checks for the presence and type of required fields: 'room_number' and
    'patient_mrn', both of which should be integers. Additional patient data
    is then processed and saved to the database.

    Parameters
    ----------
    in_data : dict
        A dictionary containing the patient data. Expected keys are:
        'room_number', 'patient_mrn', and other patient-specific data.

    Returns
    -------
    string
        Confirmation or error message.
    int
        HTTP status code (200 for success, 400 for invalid input).
    """
    expected_keys = ["room_number", "patient_mrn"]
    expected_types = [[int], [int]]
    msg = input_verification(in_data, expected_keys, expected_types)
    if msg is not True:
        return msg, 400
    new_pressure = in_data["cpap_pressure"]
    room_number = in_data["room_number"]
    print(room_number)
    new_cpap_calculations = in_data["cpap_calculations"]
    msg = cpap_pressure_validation(new_pressure)
    if msg is not True:
        return msg, 400
    else:
        return upload_patient_function(in_data)


@app.route('/lab/update_cpap_pressure', methods=['POST'])
def lab_update_cpap_pressure():
    """POST route for updating CPAP pressure for a specific room on the
    monitoring (lab) side.

    This function implements the POST route `/lab/update_cpap_pressure`. This
    POST request should receive a JSON string containing a dictionary as
    follows:

        {
            "room_number": <int of patient room number>,
            "cpap_pressure": <int containing new CPAP pressure>,
        }
    This input is sent to a driver function implementing the route and receives
    a message and status code to be returned.

    Parameters
    ----------
    None

    Returns
    -------
    string
        confirmation/error message
    int
        status code
    """
    in_data = request.get_json()
    result, status_code = lab_update_cpap_pressure_driver(in_data)
    return result, status_code


def lab_update_cpap_pressure_driver(in_data):
    """Updates CPAP pressure for a specific room on the
    monitoring (lab) side.

    This function implements the POST route `/lab/update_cpap_pressure`. It
    receives a dictionary in the form:

        {
            "room_number": <int of patient room number>,
            "cpap_pressure": <int containing new CPAP pressure>,
        }
    A generic verification is called, sending lists of the expected keys and
    expected type(s) for each key. If the verification is not successful, an
    error message and a 400 status code are returned. Next, a function
    verifying the entered CPAP pressure is an integer within the accepted range
    is called. If invalid, an error message and a 400 status code are returned.
    If successful, the patient corresponding to the room number is called and
    the CPAP pressure is updated with the new value.

    Parameters
    ----------
    in_data : dict
        dictionary containing input data described above

    Returns
    -------
    string:
        confirmation/error message
    int:
        status code
    """
    expected_keys = ["room_number", "cpap_pressure"]
    expected_types = [[int], [int]]
    msg = input_verification(in_data, expected_keys, expected_types)
    if msg is not True:
        return msg, 400
    new_pressure = in_data["cpap_pressure"]
    room_number = in_data["room_number"]
    msg = validate_room_number(room_number)
    if msg is not True:
        return msg, 400
    msg = cpap_pressure_validation(new_pressure)
    if msg is not True:
        return msg, 400
    patient = db.objects.raw({"_id": room_number}).first()
    patient.cpap_pressure = new_pressure
    patient.save()
    return "CPAP pressure successfully updated.", 200


def cpap_pressure_validation(pressure):
    """Verfies CPAP pressure input

    This function verifies that an entered CPAP pressure value is a valid
    integer between 4 and 25, inclusive. Units in cmH20. If valid, True is
    returned. If invalid, an error message is returned.

    Parameters
    ----------
    pressure : int
        input CPAP pressure

    Returns
    -------
    bool or string
        True if valid, error message if not
    """
    if type(pressure) is int and 4 <= pressure <= 25:
        return True
    return "Pressure must be an integer between 4 and 25, inclusive."


def validate_room_number(room_number):
    """Verifies occupied room number.

    This function calls the list_rooms_driver function, returning a list of
    occupied rooms. If the input room number is not found in this list an
    error message is returned. Otherwise, the function returns True.

    Parameters
    ----------
    room_number : int
        input room number

    Returns
    -------
    bool or string
        True if valid, error message if not
    """
    rooms = list_rooms_driver()[0]
    if room_number not in rooms:
        return "Patient not associated with room number entry."
    return True


@app.route('/lab/fetch_patient/<room_number>', methods=['GET'])
def fetch_patient(room_number):
    """GET route for fetching patient data from monitoring side"

    This function implements the GET `/lab/fetch_patient/<room_number>` route.
    A variable URL passes the room number through <room_number>. A driver
    function is called and a result and status code are returned. If an error
    arose during retrival, the result will be an error message and status code
    400. Otherwise, the associated patient data is returned in the form of a
    SleepLabRooms database object and a status code of 200. The result is JSON
    encoded and the status code is returned.

    Parameters
    ----------
    None

    Returns
    -------
    string
        JSON encoded result of driver function
    int
        status code
    """
    result, status_code, _patient = fetch_patient_driver(room_number)
    return jsonify(result), status_code


def fetch_patient_driver(room_number):
    """Returns patient data from associated room number

    This function implements the GET `/lab/fetch_patient/<room_number>` route.
    The string containing the room number is first converted into an integer
    using the validate_and_convert_int function. In the case of being called
    from fetch_patient this will always be a string. However, in the rare case
    the parameter cannot be converted into an integer an error message is
    returned with a status code of 400 and None. A validation function is
    called to verify the existence of patient data associated with the input
    room number. If no data is present, the error message from
    validate_room_number is returned with a status code of 400 and None
    Otherwise, the validate_room_number returns True and the SleepLabRooms
    object is called from the database with the associated room number. This
    object is then converted into a dictionary for later JSON encoding. The
    dictionary containg patient data is then returned with a status code of
    200. Note the error messaged from SleepLabRooms_to_dict will never be
    returned due to the function verifying the existence of a SleepLabRooms
    instance with the input room number.

    Parameters
    ----------
    room_number : str
        string representing room number of requested patient

    Returns
    -------
    dict or str
        patient data from SleepLabRooms database object or error message
    int
        status code
    SleepLabRooms object or None
        instance of SleepLabRooms from database or None in the case of an error
    """
    valid, result = validate_and_convert_int(room_number)
    if valid is not True:
        return result, 400, None
    msg = validate_room_number(result)
    if msg is not True:
        return msg, 400, None
    patient = db.objects.raw({"_id": result}).first()
    status, result = SleepLabRooms_to_dict(patient)
    if status is not True:
        return result, 400, None
    return result, 200, patient


@app.route('/patient/fetch_pressure/<room_number>', methods=['GET'])
def fetch_patient_pressure(room_number):
    """GET route for fetching pressure data from patient side"

    This function implements the GET `/patient/fetch_pressure/<room_number>`
    route. This route is used to add constant query for pressure
    update functionality. A variable URL passes the room number through
    <room_number>. A driver function is called and a result and status code
    are returned. If an error arose during retrival, the result will be an
    error message and status code 400.
    Otherwise, the associated pressure data is returned for the room number
    and a status code of 200. The result is JSON encoded
    and the status code is returned.

    Parameters
    ----------
    None

    Returns
    -------
    fields.IntegerField()
        result of driver funtion
    int
        status code
    """
    room_int = int(room_number)
    result, status_code = fetch_pressure_driver(room_int)
    return str(result), status_code


def fetch_pressure_driver(room_number):
    """Returns patient data from associated room number

    This function implements the GET `/patient/fetch_patient/<room_number>`
    route.
    A validation function is called to verify the existence of patient data
    associated with the input room number. If no data is present, the error
    message from validate_room_number is returned with a status code of 400.
    Otherwise, the patient data is obtained in the form of a callable
    SleepLabRooms object from the imported MongoDB database and returned with
    a status code of 200.

    Parameters
    ----------
    room_number : int
        room number of requested patient

    Returns
    -------
    fields.IntegerField()
        patient pressure
    int
        status code
    """
    msg = validate_room_number(room_number)
    if msg is not True:
        return msg, 400
    patient = db.objects.raw({"_id": room_number}).first()
    patient_cpap_pressure = patient.cpap_pressure
    return patient_cpap_pressure, 200


@app.route('/reset/<int:mrn>', methods=['GET'])
def reset_patient_data(mrn):
    """
    API endpoint to reset patient data based on their MRN.

    This route handles the request to delete a patient's record from the
    database using their Medical Record Number (MRN). It returns a JSON
    response with a success message and a corresponding HTTP status code
    (200 for success, 400 for failure).

    Parameters
    ----------
    mrn : int
        The Medical Record Number of the patient.

    Returns
    -------
    Response
        A JSON response containing the operation's message and status code.
    """
    success, message = delete_patient_record(mrn)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"message": message}), 400


def delete_patient_record(mrn):
    """
    Deletes a patient's record from the database using their MRN.

    This function tries to locate a patient record in the database by their
    MRN. If found, it deletes the record and returns a success status. If
    the record does not exist, it returns a failure status and a relevant
    message.

    Parameters
    ----------
    mrn : int
        The Medical Record Number of the patient.

    Returns
    -------
    tuple
        A tuple containing a boolean indicating success or failure, and a
        message string.
    """
    try:
        # Fetch the patient record by MRN
        patient = db.objects.get({'patient_mrn': mrn})
        patient.delete()
        return True, "Patient data reset successfully"
    except db.DoesNotExist:
        return False, "Patient with MRN {} not found".format(mrn)


def file_to_b64_string(filename):
    """Converts file to base-64 string

    This function is primarily used to send image files to the lab
    monitoring client via GET `lab/fetch_patient`. A file with the given
    filename is opened and encoded as a base-64 string. The string encoding
    is then returned.

    Adapted from David Ward, Duke University

    Parameters
    ----------
    filename : string
        filename path

    Returns
    -------
    string
        base-64 encoded data
    """
    with open(filename, "rb") as image_file:
        b64_bytes = base64.b64encode(image_file.read())
    b64_string = str(b64_bytes, encoding='utf-8')
    return b64_string


def b64_string_to_file(b64_string, filename):
    """Converts a base-64 string to a file

    This function is primarily used to receive image files from the
    patient-side client. A string assumed to contain a base-64 encoding of data
    is decoded. The data is decoded and the resulting bytes are then written to
    the given filename.

    Adapted from David Ward, Duke University

    Parameters
    ----------
    b64_string : string
        base-64 encoded data
    filename : string
        name of file to be written

    Returns
    -------
    None
    """
    image_bytes = base64.b64decode(b64_string)
    with open(filename, "wb") as out_file:
        out_file.write(image_bytes)
    return None


def SleepLabRooms_to_dict(patient):
    """Converts an instance of a SleepLabRooms object to a dictionary

    Data contained in an SleepLabRooms instance must be JSON encoded and sent
    from the web server. Since a SleepLabRooms instance cannot be JSON encoded,
    this function takes the data from the fields of a SleepLabRooms instance
    and creates a dictionary to be returned. If the parameter passed to the
    function is not a SleepLabRooms instance, False and an error message are
    returned. Otherwise, the function returns True and return the associated
    dictionary.

    Parameters
    ----------
    patient : SleepLabRooms object
        SleepLabRooms instance containing data of interest

    Returns
    -------
    dict
        dictionary containing data from SleepLabRooms instance
    """
    if isinstance(patient, db) is False:
        return False, "Input must be SleepLabRooms instance."
    patient_dict = {"room_number": patient.room_number,
                    "patient_name": patient.patient_name,
                    "patient_mrn": patient.patient_mrn,
                    "cpap_pressure": patient.cpap_pressure,
                    "cpap_calculations": patient.cpap_calculations
                    }
    return True, patient_dict


def main():
    print("Server running")
    print(type(db.objects.get({"_id": 3})))
    print(fetch_patient_driver(4)[0])
    # app.run()


if __name__ == "__main__":
    main()
    app.run(host="0.0.0.0", port=5001)
