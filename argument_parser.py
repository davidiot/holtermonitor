import logging
import argparse as ap

log_levels = ['ERROR', 'INFO', 'DEBUG']


def log_level(level_string):
    """converts a string into an enum that can be read by logging.basicConfig()

    :param level_string: logging level expressed as a string of capital letters
    :return: level_int, which can be read by logging.basicConfig()
    """

    if level_string not in log_levels:
        raise ap.ArgumentTypeError(
            'invalid logging level ({0}): choose from {1}'
            .format(level_string, log_levels))

    return getattr(logging, level_string, logging.DEBUG)


def parse_arguments():
    """ parse command line arguments using argparse

    :returns: parsed arguments (args)
    """

    par = ap.ArgumentParser(description="analyzes an electrocardiogram "
                                        "produced by a Holter Monitor and "
                                        "detects premature ventricular "
                                        "contractions.",
                            formatter_class=ap.ArgumentDefaultsHelpFormatter)

    par.add_argument("--json",
                     dest="json",
                     help="JSON metadata filename",
                     default="metadata.json")

    par.add_argument("--data",
                     dest="data",
                     help="LabView data filename",
                     default="pvcs.lvm")

    par.add_argument("--path",
                     dest="path",
                     help="path to folder containing input files",
                     default="data/")

    par.add_argument("--log",
                     default='DEBUG',
                     dest='log',
                     type=log_level,
                     nargs='?',
                     help='Sets the logging level. Choose from {0}'
                          .format(log_levels))

    par.add_argument("--ui",
                     dest="ui",
                     action="store_true",
                     help="Run the program using a user interface"
                          "(invoke to turn on)")
    par.set_defaults(ui=False)

    return par.parse_args()