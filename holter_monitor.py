import logging
import argument_parser as ap
import input_reader as ir

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
        data = lvm['data']
        import matplotlib.pyplot as plt
        plt.plot(data[:, 0], data[:, 1], 'k-')
        plt.show()
