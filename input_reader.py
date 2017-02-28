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
    data = np.fromfile(file_path(folder, filename), dtype=np.float16)

    return data


def read_data(data_filename="ecg.lvm",
              folder="data/"):
    """ Reads non-lvm files.  Not used, but might be useful later.

    :param data_filename: name of binary or lvm file
    :param folder: folder where data files are kept
    :return: ecg data array, metadata dictionary
    """

    extension = os.path.splitext(data_filename)[1]
    if extension == ".lvm":
        ecg = read_lvm(data_filename, folder)
    # TODO: uncomment this if binary files are working
    # elif extension == ".bin":
    #     ecg = read_bin(data_filename, folder)
    else:
        message = extension + " files are not supported yet"
        log.error(message)
        raise hme.InvalidFormatError(message)

    log.debug("successfully read and constructed ecg data from " +
              data_filename)

    return ecg


def file_path(folder, filename):
    """ returns the complete path to the file by concatenating the folder

    :param folder: name of folder
    :param filename: name of file
    :return: relative path of file
    """
    folder_path = "./" if len(folder) == 0 else folder
    return folder_path + filename
