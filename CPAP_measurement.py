import logging
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy import integrate
import json
import math

# Make sure it changed to bpm not bps

AIR_DENSITY = 1.199
OUTER_DIAMETER = 0.015
INNER_DIAMETER = 0.012
OUTER_AREA = np.pi * (OUTER_DIAMETER/2)**2
INNER_AREA = np.pi * (INNER_DIAMETER/2)**2

FILENAME = "patient_08"


def adc_to_pressure(adc):
    '''Calculate pressure from ADC readings.

    The CPAP machine reports pressure readings in ADC units. From the spec
    sheet, the following conversion gives a pressure reading in cm-H2O from
    ADC units:

    Pressure (cm-H2O) = [(25.4) / (14745 - 1638)] * (ADC_value - 1638)

    Pressure can then be converted into Pascals (Pa) via the conversion 1
    cm-H2O = 98.0665 Pa.

    Args:
        adc (int): ADC reading of measured pressure

    Returns:
        pressure (float): converted pressure reading in Pascals (Pa)
    '''
    try:
        pressure = (float)((25.4) / (14745 - 1638)) * (adc - 1638) * 98.0665
        pressure = round(pressure, 3)
    except TypeError:
        pressure = None
    return pressure


def determine_flow(p1_ins, p1_exp):
    '''Determines parameters for calculating volumetric air flow.

    If p1_ins is greater than or equal to p1_exp, the flow is moving towards
    the patient. p1_ins is used as p1 in the Bernoulli equation and the flow
    rate Q is postive.

    If p1_ins is less than p1_exp, the flow rate is moving away from the
    patient. p1_exp is used as p1 in the Bernoulli equation and the flow rate
    Q is negative.

    Args:
        p1_ins (float): pressure of venturi 1 (patient-side during
        inspiration) (Pa)
        p1_exp (float): pressure of venturi 1 (patient-side during
        expiration) (Pa)

    Returns:
        result (tuple) containing

        - p1 (float): upstream pressure to be used in Bernoulli equation (Pa)
        - flow_sign (int); sign of flow rate Q
    '''
    try:
        if p1_ins >= p1_exp:
            p1 = p1_ins
            flow_sign = 1
        else:
            p1 = p1_exp
            flow_sign = -1
        result = (p1, flow_sign)
    except TypeError:
        result = None
    else:
        if type(p1) in (int, float):
            return result
    return None


def volumetric_flow(p2, p1_ins, p1_exp):
    '''Calculates volumetric flow rate in L/sec given venturi pressures.

    The flow rate in m^3/sec can be determine from the Bernoulli equation

    Q = A1 * sqrt((2/rho) * (p1 - p2)/((a1/a2)^2 - 1))

    where
    Q is the volumetric flow rate (m^3/sec),
    A1 is the upstream cross-sectional area (m^2),
    A2 is the cross-sectional area at the constriction (m^2),
    rho is the density of air (kg/m^3)
    p1 is the upstream pressure (Pa)
    p2 is the pressure at the constriction (Pa).

    p1 and the sign of Q is determined from the determine_flow() function,
    where inspiration values are positive, and expiration values are negative.

    The conversion factor 1 m^3 = 1000 L is used to convert flow rate from
    m^3/sec to L/sec.

    Args:
        p2 (float): pressure at the constriction (Pa)
        p1_ins (float): pressure of venturi 1 (patient-side during
        inspiration) (Pa)
        p1_exp (float): pressure of venturi 1 (patient-side during
        expiration) (Pa)

    Returns:
        flow_rate (float): volumetric flow rate in L/sec
    '''
    a1 = OUTER_AREA
    a2 = INNER_AREA
    rho = AIR_DENSITY
    try:
        p1, flow_sign = determine_flow(p1_ins, p1_exp)
        flow_rate = 1000.0 * flow_sign * a1 * np.sqrt((2/rho)*(p1 - p2) /
                                                      ((a1/a2)**2 - 1))
        flow_rate = round(flow_rate, 3)
    except TypeError:
        flow_rate = None
    return flow_rate


def parse_line(line):
    '''Parses lines from CPAP datafile.

    Each line in the CPAP datafile should contain 7 measurements, comma
    delimited:

    Time (seconds), and 6 ADC readings corresponding to:

    - p_2 pressure of venturi 1 (patient-side)
    - p_1,ins pressure of venturi 1 (patient-side during inspiration)
    - p_1,exp pressure of venturi 1 (patient-side during expiration)
    - p_2 pressure of venturi 2 (CPAP-side)
    - p_1,ins pressure of venturi 2 (CPAP-side during inspiration)
    - p_1,exp pressure of venturi 2 (CPAP-side during expiration)

    A line is parsed and properly converted into a list containing one float
    followed by 6 ints. Any bad data or incorrectly formatted lines will
    return None.

    Args:
        line (str): line from datafile

    Returns:
        data (list) containing

        - float: time (s)
        - int: ADC pressure of venturi 1 (patient-side)
        - int: ADC pressure of venturi 1 (patient-side during inspiration)
        - int: ADC pressure of venturi 1 (patient-side during expiration)
        - int: ADC pressure of venturi 2 (CPAP-side)
        - int: ADC pressure of venturi 2 (CPAP-side during inspiration)
        - int: ADC pressure of venturi 2 (CPAP-side during expiration)
    '''
    try:
        parsed_line = line.split(",")
    except (TypeError, AttributeError):
        return None
    if len(parsed_line) != 7:
        return None
    else:
        try:
            data = []
            data.append(float(parsed_line[0]))
            data.extend([int(x) for x in parsed_line[1:]])
        except ValueError:
            return None
    return data


def calculate_metrics(time, peaks):
    '''Determine CPAP metrics from peak-finding data

    Given the time array produced from parsing the CPAP datafile and the
    peak-finding data from the calculated flow-rate profile, a Python
    dictionary is produced with the following metrics:

    - duration: time elapsed in raw data (sec)
    - breaths: number of breaths recorded in data
    - breath rate: average breathing rate determined from data in breaths/min
    - breath times: identified times of each recorded breath
    - apnea count: number of determined apnea events in data
      (an apnea event is defined as a period of 10 sec without any breaths)
    - leakage: volume of mask leakage (L)

    The leakage key-value pair is created in the returned dict, but is not
    determined. The returned dict must be passed to the examine_leakage()
    function to calculate mask leakage and change the "leakage" value from None
    to the appropriate value. The indices in the peaks list must not exceed the
    size of the time list.

    Args:
        time (list): time values determined from datafile
        peaks (list): indices of determined peaks in flow-rate data

    Returns:
        metrics (dict): calculated information from flow versus time data
    '''
    try:
        duration = round(time[-1] - time[0], 3)
        breaths = len(peaks)
        breath_rate_bpm = 60 * float(breaths/duration)
        breath_rate_bpm = round(breath_rate_bpm, 3)
        breath_times = [time[i] for i in peaks]
        apnea_count = 0
        for i in range(len(breath_times) - 1):
            if breath_times[i+1] - breath_times[i] >= 10.0:
                apnea_count += 1
    except (ValueError, TypeError, IndexError):
        return None
    metrics = {"duration": duration,
               "breaths": breaths,
               "breath_rate_bpm": breath_rate_bpm,
               "breath_times": breath_times,
               "apnea_count": apnea_count,
               "leakage": None}
    return metrics


def examine_leakage(time, flow_rate, metrics):
    '''Calculate mask leakage and store value in metrics data

    Leaks in the mask seal can be determined from examining the flow-rate
    versus time data. In a sealed system, the total net flow should be zero
    indicating no leakage. Total net flow can be determined from integrating
    the flow-rate data over time. The leakage volume in liters in determined
    from this method and returned by the function. The existinf metrics
    dictionary is passed to the function, and the "leakage" key-value pair
    is modified with the calculated value. If leakage is negative, a warning
    log entry is added. Time and flow-rate lists must be of the same size.

    Args:
        time (list): time values determined from datafile
        flow_rate (list): flow-rate values determined from datafile
        metrics (dict): calculated information from flow versus time data

    Returns:
        leakage (float): leakage volume (L)
    '''
    try:
        leakage = integrate.cumulative_trapezoid(flow_rate, time)
        while math.isnan(leakage[-1]):
            leakage = leakage[:-1]
        leakage = round(leakage[-1], 3)
        if "leakage" in metrics:
            metrics["leakage"] = leakage
            return leakage
        else:
            return None
    except (ValueError, TypeError):
        return None


def process_cpap_data(file):
    """
    Process the CPAP data from the given file path.

    Args:
        file (str): The path to the CPAP data file.

    Returns:
        dict: A dictionary containing breath rate and apnea count.
    """
    Q, time = [], []
    for line in file:
        data = parse_line(line)
        if data is None:
            logging.error("Incorrect/missing data, skipping entry.")
        else:
            time.append(data[0])
            p = [adc_to_pressure(x) for x in data[1:4]]
            flow = volumetric_flow(p[0], p[1], p[2])
            Q.append(flow)

    peaks, _ = find_peaks(Q, distance=80, prominence=0.1, height=0.1, width=20)
    metrics = calculate_metrics(time, peaks)
    leakage = examine_leakage(time, Q, metrics)
    if leakage < 0.0:
        logging.warning("Leakage is negative.")
    result = {
        "breath_rate_bpm": metrics["breath_rate_bpm"],
        "apnea_count": metrics["apnea_count"]
    }

    # Generate and save plot
    plt.figure()
    plt.plot(time, Q)
    plt.xlabel('Time (s)')
    plt.ylabel('Flow Rate (L/sec)')
    plt.title('Flow Rate vs Time')
    plot_filename = "flow_rate_vs_time_plot.png"
    plt.savefig(plot_filename)

    return plot_filename, result


def main():
    f = open("sample_data/" + FILENAME + ".txt", 'r')
    Q, time = [], []
    logging.basicConfig(filename=FILENAME + ".log", level=logging.INFO,
                        filemode='w')
    logging.info("Input file: " + FILENAME + ".txt")
    logging.info("Beginning data analysis...")
    for str in f.readlines():
        data = parse_line(str)
        if data is None:
            logging.error("Incorrect/missing data, skipping entry.")
        else:
            time.append(data[0])
            p = [adc_to_pressure(x) for x in data[1:4]]
            flow = volumetric_flow(p[0], p[1], p[2])
            Q.append(flow)
    f.close()
    peaks, pdict = find_peaks(Q, distance=80, prominence=0.1, height=0.1,
                              width=20)
    metrics = calculate_metrics(time, peaks)
    leakage = examine_leakage(time, Q, metrics)
    if leakage < 0.0:
        logging.warning("Leakage is negative.")
    out_file = open(FILENAME + ".json", "w")
    json.dump(metrics, out_file)
    out_file.close()
    logging.info("Analysis complete. Metrics available in " + FILENAME +
                 ".json")


if __name__ == "__main__":
    main()
