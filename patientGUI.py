import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from CPAP_measurement import *
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import base64

server = "http://vcm-35079.vm.duke.edu:5001"
# server = "http://127.0.0.1:8000"

breath_rate_bpm = None
apnea_count = None
gui_pressure = None
room_number_upload = None


def safe_int_conversion(text):
    """
    Safely converts a text string to an integer, returning None on failure.

    This function attempts to convert the given text string to an integer.
    If the conversion fails due to a ValueError (e.g., if the text is not
    purely numerical), the function catches the exception and returns None
    instead of raising an error.

    Parameters
    ----------
    text : str
        The text string to be converted to an integer.

    Returns
    -------
    int or None
        The converted integer value, or None if conversion fails.
    """
    try:
        return int(text)
    except ValueError:
        # Handle the error or return a default value like None or 0
        return None


def file_to_b64_string(filename):
    # Tested in test_server.py
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


def load_and_display_image(image_path, label_widget):
    """
    Loads an image from a path and displays it in a label widget.

    This function opens an image file from `image_path` using Pillow,
    converts it to a format compatible with Tkinter, and sets it in the
    `label_widget`. It's important to keep a reference to the image to
    avoid garbage collection.

    Parameters
    ----------
    image_path : str
        The file path of the image to be loaded.
    label_widget : Tkinter Label
        The Tkinter Label widget for displaying the image.

    Returns
    -------
    None
        The function does not return anything but displays the image
        in the label.
    """
    img = Image.open(image_path)
    img_tk = ImageTk.PhotoImage(img)
    label_widget.config(image=img_tk)
    label_widget.image = img_tk  # Keep a reference


def apnea_count_color(count):
    """
    Help with testing of update_apnea_count_label.

    This function is used to help the testing function and is the same
    logic as the function meantioned above.

    Parameters
    ----------
    count : int
        The current apnea event count for the label.

    Returns
    -------
    None
        The function updates the apnea events label with color.
    """

    if count >= 2:
        print("red")
    else:
        print("black")


def main_window():
    """GUI for the Patient Side Application

    This is the GUI side function that uses tkinter.
    This GUI has many helper functions each with docstrings.
    This function is called in main and runs a GUI with
    reset, upload, update, CPAP analysis, name bio entry,
    locking functionality and more. See each individual docstring
    for more information.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """

    def format_date(datetime_obj):
        # Tested in test_server.py
        """Converts datetime objects an appropriately formatted string
        representation.

        Timestamps of posted requests or results are stored in the server
        database. This function converts datetime objects
        in the datetime module to a desired string representation.

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

    def validate_cpap_pressure(pressure):
        # Tested in test_server.py
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

    def update_apnea_count_label(count):
        # Tested using mock function above
        """
        Updates the apnea events label with the current count and text color.

        This function updates `apnea_events_label` with the apnea event count.
        If the count is 2 or more, the label's text color changes to red,
        indicating more events. Otherwise, it's set to black.

        Parameters
        ----------
        count : int
            The current apnea event count for the label.

        Returns
        -------
        None
            The function updates the apnea events label in the GUI
            but returns nothing.
        """

        apnea_events_label.config(text=str(count))
        if count >= 2:
            apnea_events_label.config(fg="red")
        else:
            apnea_events_label.config(fg="black")

    def select_file():
        """
        Selects a file for processing and updates GUI with CPAP data results.

        This function opens a file dialog for the user to select a file.
        If a file
        is selected, it processes the CPAP data using the plot and outputs
        necessary information. It updates global variables for breath rate and
        apnea count, and also updates corresponding GUI labels and image.

        Returns
        -------
        tuple
            A tuple containing the plot filename and a dictionary of results,
            or None if no file is selected.
        """
        file = filedialog.askopenfile()
        if file == "":
            return
        global plot_filename
        # processes the cpap data using the plot and
        # outputs necessary information
        try:
            plot_filename, results = process_cpap_data(file)
        except TypeError:
            plot_filename = results = "No CPAP data uploaded."
        print(results)
        global breath_rate_bpm
        breath_rate_bpm = results["breath_rate_bpm"]
        global apnea_count
        apnea_count = results["apnea_count"]
        breathing_rate_label.config(text=str(breath_rate_bpm))
        update_apnea_count_label(apnea_count)
        load_and_display_image(plot_filename, cpap_flow_image)
        return plot_filename, results

    def safe_int_conversion(text):
        # Tested using function above
        """
        Safely converts a text string to an integer, returning None on failure.

        This function attempts to convert the given text string to an integer.
        If the conversion fails due to a ValueError (e.g., if the text is not
        purely numerical), the function catches the exception and returns None
        instead of raising an error.

        Parameters
        ----------
        text : str
            The text string to be converted to an integer.

        Returns
        -------
        int or None
            The converted integer value, or None if conversion fails.
        """
        try:
            return int(text)
        except ValueError:
            # Handle the error or return a default value like None or 0
            return None

    def update_gui_after_upload():
        """
        Updates GUI elements after patient data upload.

        This function disables input fields for patient MRN and room number
        after a successful data upload. It also retrieves and shows the
        current CPAP pressure in a label on the GUI.

        Returns
        -------
        None
            The function doesn't return a value but updates GUI elements.
        """
        print("Patient added")
        patient_mrn.config(state=tk.DISABLED)
        room_number.config(state=tk.DISABLED)
        gui_pressure = cpap_pressure.get()
        cpap_events_label.config(text=gui_pressure)

    def upload_data():
        """
        Uploads patient data to a server and updates the GUI upon
        successful upload.

        This function compiles patient data including room number,
        name, medical
        record number (MRN), CPAP pressure, and CPAP calculations
        (including time, breath rate, apnea count, and plot filename).
        It then sends this
        data to a
        server. If the upload is successful (indicated by a 200 status code),
        the GUI is updated to reflect this state.

        Returns
        -------
        None
            The function does not return a value, but prints the
            server response and updates the GUI upon successful
            data upload.
        """
        current_time = datetime.now()
        formatted_time = format_date(current_time)
        global gui_pressure
        gui_pressure = cpap_pressure.get()
        global room_number_upload
        room_number_upload = room_number.get()
        try:
            plot_b64 = file_to_b64_string(plot_filename)
        except NameError:
            plot_b64 = "No Image Uploaded"
        out_dict = {
            "room_number": safe_int_conversion(room_number.get()),
            "patient_name": patient_name.get(),
            "patient_mrn": safe_int_conversion(patient_mrn.get()),
            "cpap_pressure": safe_int_conversion(gui_pressure),
            "cpap_calculations": [
                formatted_time, breath_rate_bpm,
                apnea_count, plot_b64
            ]
        }
        r = requests.post(server + "/patient/upload_patient", json=out_dict)
        print(r.text)
        print(r.status_code)
        if r.status_code == 200:
            update_gui_after_upload()

    def reset_gui():
        """
        Resets the GUI elements to their default state.

        This function clears the text from input fields like patient name, CPAP
        pressure, patient MRN, and room number. It also sets the state of the
        patient MRN and room number input fields to normal (editable).
        Additionally,
        it resets the text of various labels (breathing rate, CPAP events, and
        apnea events) and updates the CPAP flow image placeholder.

        Returns
        -------
        None
            The function does not return a value but resets the GUI elements to
            their default state.
        """
        patient_name.delete(0, tk.END)
        cpap_pressure.delete(0, tk.END)
        patient_mrn.config(state=tk.NORMAL)
        room_number.config(state=tk.NORMAL)
        patient_mrn.delete(0, tk.END)
        room_number.delete(0, tk.END)
        breathing_rate_label.config(text="")
        cpap_events_label.config(text="")
        apnea_events_label.config(text="")
        cpap_flow_image.config(image='', text="CPAP Flow Image Here")

    def reset_device():
        """
        Resets the device settings for a patient and updates the GUI.

        This function sends a request to the server to reset the device
        settings for the patient specified by their medical record number
        (MRN). If the reset is successful (indicated by a 200 status code),
        the GUI is reset to its default state.

        Returns
        -------
        None
            The function does not return any value but prints the server
            response and updates the GUI upon successful device reset.
        """
        r2 = requests.get(server + '/reset/' + str(patient_mrn.get()))
        print(r2.text)
        print(r2.status_code)
        if r2.status_code == 200:
            reset_gui()

    def update_patient_info():
        # Placeholder function for updating patient information
        upload_data()

    def contact_server():
        """
        Contacts the server to fetch and update CPAP pressure in the GUI.

        This function sends a request to the server to fetch the CPAP pressure
        for the patient identified by their room number. If successful, it
        updates the CPAP events label in the GUI with this information and
        schedules the function to run again after 25 seconds. Handles TypeError
        and ValueError by printing a message and rescheduling the call.

        Returns
        -------
        None
            The function does not return any value but updates the GUI and
            periodically contacts the server.
        """
        try:
            room_num = int(room_number_upload)
            print("contacting server to check for incoming pressure")
            r1 = requests.get(
                server + '/patient/fetch_pressure/' + str(room_num))
            print(r1.text)
            print(r1.status_code)
            gui_pressure = r1.text
            cpap_events_label.config(text=gui_pressure)
            root.after(25000, contact_server)
        except TypeError:
            print("Patient not specified in database yet")
            root.after(25000, contact_server)
        except ValueError:
            print("Patient not specified in database yet")
            root.after(25000, contact_server)

    root = tk.Tk()
    root.title("CPAP Machine Patient Interface")

    # Validator for CPAP pressure entry
    vcmd = root.register(validate_cpap_pressure)

    # Patient Information
    tk.Label(root, text="Patient Name:").grid(row=0, column=0)
    patient_name = tk.Entry(root)
    patient_name.grid(row=0, column=1)

    tk.Label(root, text="MRN:").grid(row=1, column=0)
    patient_mrn = tk.Entry(root)
    patient_mrn.grid(row=1, column=1)

    tk.Label(root, text="Room Number:").grid(row=2, column=0)
    room_number = tk.Entry(root)
    room_number.grid(row=2, column=1)

    # CPAP Settings
    tk.Label(root, text="CPAP Pressure (4-25 cmH2O):").grid(row=3, column=0)
    cpap_pressure = tk.Entry(root, validate="key",
                             validatecommand=(vcmd, '%P'))
    cpap_pressure.grid(row=3, column=1)
    cpap_events_label = tk.Label(root, text=str(gui_pressure))
    cpap_events_label.grid(row=3, column=2)

    tk.Button(root, text="Select CPAP Data File", command=select_file).grid(
        row=4, column=0, columnspan=2)

    # Calculated Data Display
    tk.Label(root, text="Breathing Rate:").grid(row=5, column=0)
    breathing_rate_label = tk.Label(root, text=str(breath_rate_bpm))
    breathing_rate_label.grid(row=5, column=1)

    tk.Label(root, text="Number of Apnea Events:").grid(row=6, column=0)
    apnea_events_label = tk.Label(root, text=str(apnea_count))
    apnea_events_label.grid(row=6, column=1)

    # CPAP Flow Image Display (Placeholder)
    cpap_flow_image = tk.Label(root, text="CPAP Flow Image Here")
    cpap_flow_image.grid(row=7, column=0, columnspan=2)

    # Control Buttons
    tk.Button(root, text="Upload Data",
              command=upload_data).grid(row=8, column=0)
    tk.Button(root, text="Reset Device",
              command=reset_device).grid(row=8, column=1)
    tk.Button(root, text="Update Patient Info", command=upload_data).grid(
        row=9, column=0, columnspan=2)

    root.after(3000, contact_server)
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main_window()
