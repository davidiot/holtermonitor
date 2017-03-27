import logging
import argument_parser as ap
import input_reader as ir
import waveform_plotter as wp

args = ap.parse_arguments()

logging.basicConfig(
    filename="holter_monitor_log.txt",
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=args.log)

log = logging.getLogger("hm_logger")

log.debug(args)

if args.ui:
    pass
else:
    time, ecg = ir.read_data(args.data, args.path)
    # import matplotlib.pyplot as plt
    # plt.plot(data)
    # plt.show()
    import numpy as np
    pvcs = np.array(
        [[13495, 55],
         [19406, 42],
         [25305, 73],
         [143498, 64],
         [149402, 36],
         [155301, 81]])
    # wp.render_pvc_plot(time, ecg, pvcs)
    wp.render_full_plot(time, ecg, pvcs)
