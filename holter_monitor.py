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
        lvm = ir.read_lvm(args.data, args.path)
        import numpy as np
        wp.render_interactive_plot(lvm, np.array(
            [[500, 55], [2400, 35], [3000, 95], [3600, 5], [4750, 42]]))
