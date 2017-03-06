import holter_monitor_errors as hme
import numpy as np
import lvm_read as lr
import os.path
import logging
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

    return data[0]['data']


def read_bin(filename="ecg.npy", folder="data/"):
    """ reads ecg data from a NumPy (.npy) binary file

    :param filename: name of binary file
    :param folder: folder where data files are kept
    :return: ecg data array
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".npy":
        message = filename + " was not a NumPy binary file"
        log.error(message)
        raise hme.InvalidFormatError(message)
    data = np.load(file_path(folder, filename))

    return data


def read_data(data_filename="ecg.lvm",
              folder="data/"):
    """ Read data from a file

    :param data_filename: name of npy or lvm file
    :param folder: folder where data files are kept
    :return: ecg data array
    """

    extension = os.path.splitext(data_filename)[1]
    if extension == ".lvm":
        ecg = read_lvm(data_filename, folder)
    elif extension == ".npy":
        ecg = read_bin(data_filename, folder)
    else:
        message = extension + " files are not supported yet"
        log.error(message)
        raise hme.InvalidFormatError(message)

    log.debug("successfully read and constructed ecg data from " +
              data_filename)

    return ecg.astype("float32")


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
