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
    else:
        data = ir.read_data(args.data, args.path)
        import numpy as np
        # import matplotlib.pyplot as plt
        # plt.plot(data)
        # plt.show()
        wp.render_pvc_plot(data, np.array(
            [[12000, 55],
             [17750, 42],
             [23800, 73],
             [141800, 64],
             [148000, 36],
             [154000, 81]]))
