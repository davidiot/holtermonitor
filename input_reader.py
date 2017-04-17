import holter_monitor_errors as hme
import holter_monitor_constants as hmc
import numpy as np
import lvm_read as lr
import nptdms as npt
import os.path
import logging
log = logging.getLogger("hm_logger")


def read_tdms(filename="ecg.tdms", folder="data/",
              sample_rate=hmc.SAMPLE_RATE,
              group_name="GroupName",
              channel_name="ChName"):
    """ reads ecg data from an LabView TDMS (.tdms) file

    :param filename: name of tdms file
    :param folder: folder where data files are kept
    :param sample_rate: sampling rate of the tdms file
    :param group_name: group name of the channel to read from in the TDMS file
    :param channel_name: name of the channel to read from in the group
    :return: time data array, ecg data array
    """
    extension = os.path.splitext(filename)[1]
    if extension != ".tdms":
        message = filename + " was not a TDMS file"
        log.error(message)
        raise hme.InvalidFormatError(message)

    file = npt.TdmsFile(file_path(folder, filename))
    ecg = file.object(group_name, channel_name).data
    num_samples = len(ecg)
    num_seconds = num_samples / sample_rate
    time = np.linspace(0, num_seconds, num_samples)
    return time, ecg


def read_lvm(filename="ecg.lvm", folder="data/"):
    """ reads ecg data from an LabView (.lvm) file

    :param filename: name of lvm file
    :param folder: folder where data files are kept
    :return: time data array, ecg data array
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

    arr = data[0]['data']
    ecg = arr[:, 1]
    time = arr[:, 0]
    return time, ecg


def read_bin(filename="ecg.npy", folder="data/"):
    """ reads ecg data from a NumPy (.npy) binary file

    :param filename: name of binary file
    :param folder: folder where data files are kept
    :return: time data array, ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".npy":
        message = filename + " was not a NumPy binary file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    data = np.load(file_path(folder, filename))
    time = data[:, 0]
    ecg = data[:, 1]
    return time, ecg


def read_txt(filename="ecg.txt", folder="data/",
             sample_rate=hmc.SAMPLE_RATE):
    """ reads ecg data from a text file generated using the memory system
    
    :param filename: name of .txt file
    :param folder: folder where data files are kept
    :param sample_rate: sampling rate of the data
    :return: time data array, ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".txt":
        message = filename + " was not a .txt file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    with open(file_path(folder, filename)) as f:
        lines = f.read().splitlines()
        ecg = np.array([int(i) for i in lines])
        num_samples = len(ecg)
        num_seconds = num_samples / sample_rate
        time = np.linspace(0, num_seconds, num_samples)
        return time, ecg


def read_data(data_filename="ecg.lvm",
              folder="data/"):
    """ Read data from a file

    :param data_filename: name of npy or lvm file
    :param folder: folder where data files are kept
    :return: time data array, ecg data array
    """

    extension = os.path.splitext(data_filename)[1]
    if extension == ".lvm":
        time, ecg = read_lvm(data_filename, folder)
    elif extension == ".npy":
        time, ecg = read_bin(data_filename, folder)
    elif extension == ".tdms":
        time, ecg = read_tdms(data_filename, folder)
    elif extension == ".txt":
        time, ecg = read_txt(data_filename, folder)
    else:
        message = extension + " files are not supported yet"
        log.error(message)
        raise hme.InvalidFormatError(message)

    log.debug("successfully read and constructed ecg data from " +
              data_filename)

    return time.astype("float32"), ecg.astype("float32")


def file_path(folder, filename):
    """ returns the complete path to the file by concatenating the folder

    :param folder: name of folder
    :param filename: name of file
    :return: relative path of file
    """
    folder_path = "./" if len(folder) == 0 else folder
    return folder_path + filename


def save_binary(data, input_filename, output_filename, folder="data/"):
    input_extension = os.path.splitext(input_filename)[1]
    if input_extension == ".npy":
        message = "input file was already a NumPy binary file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    output_extension = os.path.splitext(output_filename)[1]
    if output_extension != ".npy":
        message = "output file is not a NumPy binary file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    output_file = open(file_path(folder, output_filename), 'wb')
    np.save(output_file, data)
    output_file.close()
