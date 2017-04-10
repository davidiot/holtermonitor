import logging
import argument_parser as ap
import input_reader as ir
import waveform_plotter as wp
import database_manager as dm
import pvc_detect_two as pvc_detect
import holter_monitor_constants as hmc

args = ap.parse_arguments()

logging.basicConfig(
    filename="holter_monitor_log.txt",
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=args.log)

log = logging.getLogger("hm_logger")

if args.upload:
    time, ecg = ir.read_data(args.upload, args.path)
    pvcs = pvc_detect.process_data(hmc.SAMPLE_RATE, args.pvc_window, ecg)
    dm.upload(time, ecg, pvcs)

else:
    # import matplotlib.pyplot as plt
    # plt.plot(data)
    # plt.show()
    # time, ecg = ir.read_data(args.data, args.path)
    # wp.render_pvc_plot(time, ecg, pvcs)
    wp.render_full_plot()
