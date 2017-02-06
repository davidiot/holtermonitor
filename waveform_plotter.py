import matplotlib as mpl
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import bisect as bis
from mpld3 import plugins, utils


class LinkedView(plugins.PluginBase):
    """ A plugin for linking the timeline to the EKG plot.

    """

    JAVASCRIPT = """
    mpld3.register_plugin("linkedview", LinkedViewPlugin);
    LinkedViewPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    LinkedViewPlugin.prototype.constructor = LinkedViewPlugin;
    LinkedViewPlugin.prototype.requiredProps = ["idpts", "idline", "data"];
    LinkedViewPlugin.prototype.defaultProps = {}
    function LinkedViewPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    LinkedViewPlugin.prototype.draw = function(){
      var pts = mpld3.get_element(this.props.idpts);
      var line = mpld3.get_element(this.props.idline);
      var data = this.props.data;

      function mouseover(d, i){
        line.data = data[i];
        line.elements().transition()
            .attr("d", line.datafunc(line.data))
            .style("stroke", this.style.fill);
      }
      pts.elements().on("mouseover", mouseover);
    };
    """

    def __init__(self, points, line, linedata):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}


def render_interactive_plot(lvm, pvcs, window=3):
    """ renders an interactive plot in a browser for viewing PVCs over 24 hrs

    :param lvm: ecg data read in from an LVM file
    :param pvcs: an array that stores the indices of the detected PVCs
    :param window: the number of seconds of EKG to display in the top window
    :return:
    """

    data = lvm['data']
    ecg = data[:, 1]
    time = data[:, 0]
    time_range = time[len(time) - 1]
    fig, ax = plt.subplots(2)
    window_range = bis.bisect_left(time, window)

    units = 'seconds'
    divisor = 1
    if time_range > 10800:  # 3 hours
        units = 'hours'
        divisor = 3600
    elif time_range > 180:  # 3 minutes
        units = 'minutes'
        divisor = 60

    # set up timeline
    ax[1].set_xlim(0, time_range / divisor)
    ax[1].set_ylim(0, 100)
    ax[1].yaxis.set_major_formatter(plt.NullFormatter())
    ax[1].yaxis.set_ticks([])
    ax[1].set_xlabel('Timeline (' + units + ')')
    ax[1].set_ylabel('PVC %')
    ax[0].set_title("PVC Analyzer")

    pvc_indices = pvcs[:, 0]
    pvc_times = np.take(time, pvc_indices) / divisor
    pvc_strengths = pvcs[:, 1]
    ax[1].vlines(pvc_times, np.zeros(len(pvc_times)), pvc_strengths)
    points = ax[1].scatter(pvc_times,
                           pvc_strengths,
                           c=pvc_strengths,
                           s=250, alpha=0.7)

    # create the line and data objects
    x = np.take(time, range(0, window_range))
    waveform_data = \
        np.array(
            [[x,
              np.take(ecg,
                      range(index, index + window_range)
                      if index + window_range <= len(ecg)
                      else range(len(ecg) - window_range, len(ecg)))]
             for index in pvc_indices])
    lines = ax[0].plot(x, 0 * x, '-w', lw=3, alpha=0.5)
    ax[0].set_ylim(0, 2)

    # transpose line data and add plugin
    linedata = waveform_data.transpose(0, 2, 1).tolist()
    plugins.connect(fig, LinkedView(points, lines[0], linedata))
    mpld3.show()
