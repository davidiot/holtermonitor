import holter_monitor_errors as hme
import dateutil.parser as dup
import numpy as np
import lvm_read as lr
import os.path
import logging
import h5py
import json
from scipy.io import loadmat
log = logging.getLogger("hm_logger")


def read_lvm(filename="ecg.lvm", folder="data/"):
    """ reads ecg data from an LabView (.lvm) file

    :param filename: name of lvm file
    :param folder: folder where data files are kept
    :return: ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".lvm":
        message = filename + " was not a LabView file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    data = lr.read(file_path(folder, filename))

    if data["Segments"] != 1:
        message = "multiple segments detected in " + filename
        log.error(message)
        raise hme.InvalidFormatError(message)

    log.debug("successfully read and constructed ecg data from " + filename)
    return data[0]


def read_json(filename="metadata.json", folder="data/",
              fs="sampling_rate", start="start_time", units="units"):
    """reads data acquisition metadata from a json file

    :param filename: name of JSON file
    :param folder: folder where data files are kept
    :param fs: JSON key corresponding to sampling rate in Hz
    :param start: JSON key corresponding to start time of data acquisition
    :param units: JSON key corresponding to units ECG signal
    :return: data dict wth fs, start time, and units
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".json":
        message = filename + " was not a json file"
        log.error(message)
        raise hme.InvalidFormatError(message)

    with open(file_path(folder, filename), 'r') as json_data:
        data = json.load(json_data)

    for key in [fs]:  # using an array in case we need other numerical values
        try:
            data[key] = float(data[key])
            assert(data[key] > 0)
        except KeyError:
            message = filename + " is missing key " + key
            log.error(message)
            raise hme.MissingDataError(message)
        except ValueError:
            message = filename + " has non-numerical " + key + " value."
            log.error(message)
            raise hme.DataFormatError(message)
        except AssertionError:
            message = filename + " has negative or zero " + key + " value."
            log.error(message)
            raise hme.DataFormatError(message)

    if start not in data:
        message = filename + " is missing key " + start
        log.error(message)
        raise hme.MissingDataError(message)

    data[start] = dup.parse(data[start])

    if units not in data:
        message = filename + " is missing key " + units
        log.error(message)
        raise hme.MissingDataError(message)

    data[units] = str(data[units])

    log.debug("successfully loaded " + filename)
    return data


def read_data(json_filename="metadata.json",
              data_filename="ecg.lvm",
              folder="data/"):
    """ Reads non-lvm files.  Not used, but might be useful later.

    :param json_filename: name of JSON metadata file
    :param data_filename: name of binary, MATLAB, or HDF5 file
    :param folder: folder where data files are kept
    :return: ecg data array, metadata dictionary
    """

    metadata = read_json(json_filename, folder)
    extension = os.path.splitext(data_filename)[1]
    if extension == ".bin":
        ecg = read_bin(data_filename, folder)
    elif extension == ".mat":
        ecg = read_mat(data_filename, folder)
    elif extension == ".h5":
        ecg = read_hdf5(data_filename, folder)
    else:
        message = extension + " files are not supported yet"
        log.error(message)
        raise hme.InvalidFormatError(message)

    log.debug("successfully read and constructed ecg data from " +
              data_filename)

    return ecg, metadata


def file_path(folder, filename):
    """ returns the complete path to the file by concatenating the folder

    :param folder: name of folder
    :param filename: name of file
    :return: relative path of file
    """
    folder_path = "./" if len(folder) == 0 else folder
    return folder_path + filename


def check_data(data, filename):
    """ checks if data is valid

    :param data: ecg data array
    :param filename: name of file that the data came from
    :return:
    """
    if len(data) == 0:
        message = filename + " was empty"
        log.error(message)
        raise hme.MissingDataError(message)


def read_bin(filename="ecg.bin", folder="data/"):
    """ reads ecg data from a binary (.bin) file

    :param filename: name of binary file
    :param folder: folder where data files are kept
    :return: ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".bin":
        message = filename + " was not a binary file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    data = np.fromfile(file_path(folder, filename), dtype=np.int16)

    check_data(data)

    return data


def read_mat(filename="ecg.mat", folder="data/"):
    """ reads ecg data from a MATLAB (.mat) file

    :param filename: name of MATLAB file
    :param folder: folder where data files are kept
    :return: ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".mat":
        message = filename + " was not a MATLAB file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    file = loadmat(file_path(folder, filename))

    try:
        data = file['data']
    except KeyError:
        message = filename + " did not contain a 'data' key"
        log.error(message)
        raise hme.MissingDataError(message)

    check_data(data, filename)
    return data


def read_hdf5(filename="sinogram.h5", folder="data/"):
    """ reads ecg data from a HDF5 (.h5) file

    :param filename: name of HDF5 (.h5) file
    :param folder: folder where data files are kept
    :return: ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".h5":
        message = filename + " was not an HDF5 file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    with h5py.File(file_path(folder, filename), 'r') as hf:
        data = np.array(hf.get('data'))
        check_data(data, filename)
        return data