import logging
import argument_parser as ap
import input_reader as ir
import waveform_plotter as wp

if __name__ == "__main__":
    args = ap.parse_arguments()

    logging.basicConfig(
        filename="holter_monitor_log.txt",
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=args.log)

    log = logging.getLogger("hm_logger")

    if args.ui:
        pass
    elif args.convert != "":
        data = ir.read_data(args.data, args.path)
        ir.save_binary(data, args.data, args.convert, args.path)
    else:
        data = ir.read_data(args.data, args.path)
        # import matplotlib.pyplot as plt
        # plt.plot(data)
        # plt.show()
        # import numpy as np
        # wp.render_pvc_plot(data, np.array(
        #     [[13500, 55],
        #      [19250, 42],
        #      [25300, 73],
        #      [143300, 64],
        #      [149500, 36],
        #      [155500, 81]]))
        wp.render_full_plot(data)
