# final-project-suraj_lucas
final-project-suraj_lucas created by GitHub Classroom

## Patient GUI functionality

Video Demo of the Patient Side GUI Functionality: [https://youtu.be/KeNGyYvRgCQ ](https://youtu.be/X3FIjRcxxJg?feature=shared)

The Gui allows for the following functionality:
Allows the user to enter a patient name.
Allows the user to enter a patient medical record number (MRN).
Allows the user to enter a room number.
Allows the user to enter a CPAP pressure in units of cmH2O (validates that the entry is an integer and must be between 4 and 25)
Allow the user to select a CPAP data file from the local computer. This CPAP data should then be analyzed for:
    breathing rate in breaths per minute,
    number of apnea events
    flow rate vs. time
The above calculated info is displayed in the GUI along with the image of the flow rate vs. time curve. 
If the number of apnea events is two or greater, that value is displayed in red. If the number of apnea events is zero or one, it should be displayed in black. 
The GUI has three button: upload, update and reset.
The upload button uploads the patient data to the database only if the MRN and room number are present.
The update button, updates the database and the displayed CPAP pressure with any new information, but keeps the MRN and room number the same.
The GUI also preiodically checks (every 25 seconds) for any update from the monitoring side for CPAP pressure update.
The user also has the ability to "reset" the device. This means that all entries and displayed data are removed, including the patient medical record number and room number. All information is also deleted from the database. 

## Lab GUI functionality

## Server Access

You may access this server at http://vcm-35079.vm.duke.edu:5000.


## API Reference Guide
Below are all of the get and post requests implemented in this project. 
### @app.route('/lab/list_rooms', methods=['GET'])
The above route gets a list of all of the available rooms.
### @app.route('/patient/upload_patient', methods=['POST'])
The above route can be used to upload and update a patient with
all of their bio info and there CPAP calculations.
### @app.route('/lab/update_cpap_pressure', methods=['POST'])
The above route updates the CPAP pressure on the database
from the monitoring side. 
### @app.route('/lab/fetch_patient/<room_number>', methods=['GET'])
The above route fetches a patient given their room number for the
monitoring side.
### @app.route('/patient/fetch_pressure/<room_number>', methods=['GET'])
The above route fetches a patient's cpap pressure given their room number for the
monitoring side.
### @app.route('/reset/<int:mrn>', methods=['GET'])
The above route resets a patient from a room given their MRN and removes them from the database.
## Database Design
{
“Rooms” : {
“Room Number”: 1,
“Patient Name”: “John”,
“Patient MRN”: 100,
“CPAP Pressure”: 15,
“CPAP Calculations”: [[timestamp1, breathing rate, # apnea events, flow rate image], [timestamp2, breathing rate, # apnea events, flow rate image]]
}, {
“Room Number”: 2,
“Patient Name”: “Bob”,
“Patient MRN”: 101,
“CPAP Pressure”: 10,
“CPAP Calculations”: [[timestamp1, breathing rate, # apnea events, flow rate image], [timestamp2, breathing rate, # apnea events, flow rate image]]
}
}

MIT License

Copyright (c) [2023] [Suraj Dhulipalla]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
