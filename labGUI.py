import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.ttk import Label as tkl
import requests
import base64
from PIL import Image, ImageTk


server = "http://vcm-35079.vm.duke.edu:5001"
global patient
patient = {"accessed": False}


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


def tk_img_from_filename(filename):
    pil_img = Image.open(filename)
    size = pil_img.size
    pil_img = pil_img.resize((150, 150))
    tk_image = ImageTk.PhotoImage(pil_img)
    return tk_image


def format_patient(in_data):
    expected_keys = ["room_number", "patient_name", "patient_mrn",
                     "cpap_pressure", "cpap_calculations"]
    expected_types = [[int], [str], [int], [int], [list]]
    verif = input_verification(in_data, expected_keys, expected_types)
    if verif is not True:
        return False, verif
    calc_data = in_data["cpap_calculations"]
    patient["accessed"] = True
    patient["room_number"] = str(in_data["room_number"])
    patient["patient_mrn"] = str(in_data["patient_mrn"])
    patient["patient_name"] = in_data["patient_name"]
    patient["cpap_pressure"] = str(in_data["cpap_pressure"])
    calc_dict = {}
    for entry in calc_data:
        calc_dict[entry[0]] = [entry[0], str(entry[1]), str(entry[2]),
                               entry[3]]
    patient["cpap_calculations"] = calc_dict


def main_window():
    global options
    options = []
    global selected

    def fetch_data():

        def fill_calculations():
            calcs = patient["cpap_calculations"][timestamp.get()]
            tkl(root, text=calcs[1]).grid(row=16, column=1)
            apnea = tkl(root, text=calcs[2])
            apnea.grid(row=17, column=1)
            if int(calcs[2]) >= 2:
                apnea.configure(foreground="red")
            tkl(root, text=calcs[2]).grid(row=17, column=1)
            # b64_string_to_file(calcs[3], "img.png")
            tk_img = tk_img_from_filename("test_data/test_image.jpg")
            image_label = ttk.Label(root, image=tk_img)
            image_label.grid(column=0, row=18)

        if selected.get != 0:
            r = requests.get(server + "/lab/fetch_patient/" +
                             str(selected.get()))
            in_data = r.json()
            format_patient(in_data)
            tkl(root, text=patient["room_number"]).grid(row=11, column=1,
                                                        sticky="w")
            tkl(root, text=patient["patient_name"]).grid(row=12, column=1,
                                                         sticky="w")
            tkl(root, text=patient["patient_mrn"]).grid(row=13, column=1,
                                                        sticky="w")
            tkl(root, text=patient["cpap_pressure"]).grid(row=14, column=1,
                                                          sticky="w")
            tkl(root, text=str(len(patient["cpap_calculations"].keys()))).grid(
                row=15, column=1)
            if len(patient["cpap_calculations"].keys()) > 0:
                timestamps = patient["cpap_calculations"].keys()
                ttk.OptionMenu(root, timestamp, *
                               timestamps).grid(row=15, column=1)
                ttk.Button(root,
                           text="Select",
                           command=fill_calculations).grid(column=2, row=15)
            root.after(25000, fetch_data)

    root = tk.Tk()
    root.title("Lab Monitoring Station")

    tkl(root, text="Select Room Number:").grid(row=0, column=0)
    timestamp = tk.StringVar()

    ttk.Separator(root, orient="horizontal").grid(row=1, column=0,
                                                  columnspan=3, sticky="ew")
    ttk.Button(root, text="Select", command=fetch_data).grid(row=0, column=2)
    selected = tk.IntVar(value=0)
    selected.set(0)
    r = requests.get(server + "/lab/list_rooms")
    options = r.json()
    ttk.OptionMenu(root, selected, *options).grid(row=0, column=1)
    ttk.Button(root, text="Select", command=fetch_data).grid(row=0, column=2)
    ttk.OptionMenu(root, selected, *options).grid(row=0, column=1)
    tkl(root, text="Patient Room Number:").grid(row=11, column=0, sticky="w")

    tkl(root, text="Patient Name:").grid(row=12, column=0, sticky="w")

    tkl(root, text="Patient MRN:").grid(row=13, column=0, sticky="w")

    tkl(root, text="CPAP Pressure (cm-H20):").grid(row=14, column=0,
                                                   sticky="w")
    tkl(root, text="View Data From:").grid(row=15, column=0,
                                           sticky="w")
    tkl(root, text="Breathing Rate:").grid(row=16, column=0,
                                           sticky="w")
    tkl(root, text="Apnea Events:").grid(row=17, column=0,
                                         sticky="w")
    tkl(root, text="Flow Rate:").grid(row=18, column=0,
                                      sticky="w")

    root.after(3000, fetch_data)
    root.mainloop()


if __name__ == "__main__":
    main_window()
