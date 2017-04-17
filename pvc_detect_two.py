import holter_monitor_errors as hme
import numpy as np
import lvm_read as lr
import os.path
from biosppy.signals import ecg
import matplotlib.pyplot as plt
from input_reader import file_path
import array
import sys
from scipy.signal import butter, lfilter, freqz

def butter_lowpass(cutoff, fs, order=5):
   nyq = 0.5 * fs
   normal_cutoff = cutoff / nyq
   b, a = butter(order, normal_cutoff, btype='low', analog=False)
   return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
   b, a = butter_lowpass(cutoff, fs, order=order)
   y = lfilter(b, a, data)
   return y

def get_signal_data(fs, window, filename):
    """ reads ecg data from an LabView (.lvm) file and ensures proper window length

    :param fs: sampling frequency of data
    :param window: interval for average processing (seconds)
    :return: ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension == ".lvm":
        data = read_lvm(filename, "data_2/")['data']
    print("Length:", len(data))
    seconds = len(data) / fs
    if window > seconds:
        raise IndexError("Window longer than length of data")
    return data


def get_distances(r_peaks, fs):
    """ calculates RR Intervals based on R-peak locations

    :param r_peaks: data point locations of R-peaks
    :param fs: sampling frequency of data
    :return: array of RR Interval lengths
    """

    distances = [None] * (len(r_peaks) - 1)
    r_peak_times = []
    for i in range(1, len(r_peaks)):
        distances[i - 1] = r_peaks[i] - r_peaks[i - 1]
        temp = r_peaks[i] / (fs)
        r_peak_times.append(temp)
    return distances, r_peak_times


def get_indexes(r_peak_times, window):
    """ computes zero-based indexes of windows for RR-Interval averages

    :param r_peak_times: data point locations of R-peaks, in seconds
    :param window: desired window width, in seconds
    :return: array of indexes
    """

    indexes = []
    multiplier = 1
    for i in range(0, len(r_peak_times)):
        if r_peak_times[i] >= multiplier*window:
            indexes.append(i)
            multiplier += 1
    return indexes


def get_averages(distances, indexes):
    """ calculates RR Interval averages for a specific window of time

    :param distances: array of RR-Interval widths
    :param indexes: zero-based indexes defining the windows of data
    :return: array of RR Interval averages
    """

    averages = []
    averages.append(np.mean(remove_outliers(distances[0:indexes[0]])))
    for i in range(1, len(indexes)):
        removed_outliers = remove_outliers(distances[indexes[i - 1]:indexes[i]])
        average = np.mean(removed_outliers)
        averages.append(average)
    averages.append(np.mean(distances[indexes[len(indexes) - 1]:]))
    return averages


def get_mode(signal):
    """ calculates the mode of the amplitude of the original ECG signal

    :param signal: the original ECG signal
    :return: most-occuring y-value in the ECG signal
    """

    signal = np.array(signal)
    hist = np.histogram(signal)
    freqs = hist[0]
    bins = hist[1]
    max_freq = max(freqs)
    index_arr = np.where(freqs == max_freq)
    index = index_arr[0][0]
    mode = (bins[index] + bins[index + 1]) / 2
    return mode


def remove_outliers(distances):
    """ removes outliers in RR-Interval widths array

    :param distances: array of RR-Interval widths
    :return: array of RR-Interval widths with outliers removed
    """

    sorted = np.sort(distances)
    length = len(sorted)
    first = int((length) / 4)
    third = int(3 * (length) / 4)
    first_quartile = sorted[first]
    third_quartile = sorted[third]
    iqr = third_quartile - first_quartile
    dist = []

    for i in range(0, len(distances)):
        if distances[i] >= (first_quartile - 1.5 * iqr) and distances[i] <= (third_quartile + 1.5 * iqr):
            dist.append(distances[i])
    return dist


def get_y_vals(signal, pvc_indexes):
    """ obtains y-coordinates of PVC locations

    :param signal: the original ECG signal
    :param pvc_indexes: the x-coordinates of the detected PVCs
    :return: array of y-coordinates
    """

    pvc_y_vals=[]
    for i in range(0, len(pvc_indexes)):
        pvc_y_vals.append(signal[pvc_indexes[i]])
    return pvc_y_vals


def process_pvc(signal, distances, averages, indexes, r_peaks, prematurity, compensatory, dist):
    count = 0
    pvc_count = 0
    mode = get_mode(signal)
    pvc_indexes_25 = []
    pvc_indexes_50 = []
    pvc_indexes_75 = []
    pvc_indexes_100 = []

    for i in range(0, len(distances) - 2):
        if i > 0 and count < len(indexes) and i > indexes[count]:
            count += 1
        percent_error_one = (distances[i] - averages[count]) / averages[count]
        if percent_error_one <= -prematurity:
            pvc_indexes_25.append(r_peaks[i + 1])
            percent_error_two = (distances[i + 1] - averages[count]) / averages[count]
            if percent_error_two >= compensatory:
                pvc_indexes_25.pop((len(pvc_indexes_25) - 1))
                pvc_indexes_50.append(r_peaks[i + 1])
                test_dist = (distances[i + 1] + distances[i]) / 2
                test_dist_percent_error = (test_dist - averages[count]) / averages[count]
                if abs(test_dist_percent_error) <= dist:
                    pvc_indexes_50.pop((len(pvc_indexes_50) - 1))
                    #print("****PVC75****", distances[i], r_peaks[i + 1], r_peak_times[i + 1], test_dist_percent_error,
                          #test_dist, averages[count])
                    #pvc_count += 1
                    pvc_indexes_75.append(r_peaks[i + 1])
                    if signal[r_peaks[i + 1]] < mode:
                        pvc_indexes_75.pop((len(pvc_indexes_75) - 1))
                        pvc_indexes_100.append(r_peaks[i + 1])
                        pvc_count += 1
    return pvc_indexes_25, pvc_indexes_50, pvc_indexes_75, pvc_indexes_100, pvc_count


def process_data(fs, window, signal):
    """ main function for detecting PVCs

     :param fs: sampling frequency of data
     :param window: interval for average processing (seconds)
     """

    #data = get_signal_data(fs, window, ecg)
    #signal = data[:, 1]
    #signal = ecg
    #print(signal)

    y = butter_lowpass_filter(signal, cutoff=15, fs=fs, order=5)

    plt.subplot(2, 1, 1)
    plt.plot(signal, '-b')

    plt.subplot(2, 1, 2)
    plt.plot(y, '-g')
    plt.show()

    out = ecg.ecg(signal=y, sampling_rate=fs, show=False)
    r_peaks = out['rpeaks']
    filtered = out['filtered']
    distance_data = get_distances(r_peaks, fs)
    distances = distance_data[0]
    r_peak_times = distance_data[1]
    indexes = get_indexes(r_peak_times, window)
    averages = get_averages(distances, indexes)

    pvc_indexes = process_pvc(filtered, distances, averages, indexes, r_peaks, .15, .05, .2)
    pvc_indexes_25=pvc_indexes[0]
    pvc_indexes_50=pvc_indexes[1]
    pvc_indexes_75=pvc_indexes[2]
    pvc_indexes_100=pvc_indexes[3]
    pvc_count = pvc_indexes[4]

    pvc_y_vals_25 = get_y_vals(filtered, pvc_indexes_25)
    pvc_y_vals_50 = get_y_vals(filtered, pvc_indexes_50)
    pvc_y_vals_75 = get_y_vals(filtered, pvc_indexes_75)
    pvc_y_vals_100 = get_y_vals(filtered, pvc_indexes_100)

    print(pvc_count, "PVCs detected.")
    #plt.plot(filtered, '-')
    plt.plot(filtered, '-', pvc_indexes_25, pvc_y_vals_25, 'r.',  pvc_indexes_50, pvc_y_vals_50, 'c.',pvc_indexes_75, pvc_y_vals_75, 'm.', pvc_indexes_100, pvc_y_vals_100, 'g.', markersize=20)
    plt.legend(['ECG Signal', '1 PVC Criterion Met', '2 PVC Criteria Met', '3 PVC Criteria Met', 'PVC'])
    plt.title(str(pvc_count) + " PVCs detected")

    arr_25 = generate_array(pvc_indexes_25, 1)
    arr_50 = generate_array(pvc_indexes_50, 2)
    arr_75 = generate_array(pvc_indexes_75, 3)
    arr_100 = generate_array(pvc_indexes_100, 4)

    locs = arr_25+arr_50+arr_75+arr_100

    locs = sorted(locs, key=lambda tup: tup[0])

    #print(locs)
    plt.show()

    return locs

def generate_array(indexes, val):
    arr=[]
    for index in indexes:
        tuple = (index, val)
        arr.append(tuple)
    return arr


def read_lvm(filename, folder):
    """ reads ecg data from an LabView (.lvm) file

    :param filename: name of lvm file
    :param folder: folder where data files are kept
    :return: ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".lvm":
        message = filename + " was not a LabView file"
        #log.error(message)
        raise hme.InvalidFormatError(message)
    data = lr.read(file_path(folder, filename))

    if data["Segments"] != 1:
        message = "multiple segments detected in " + filename
        #log.error(message)
        raise hme.InvalidFormatError(message)

    #log.debug("successfully read and constructed ecg data from " + filename)
    return data[0]


if __name__ == '__main__':
    process_data(1000, 10, "multipvc.lvm")
