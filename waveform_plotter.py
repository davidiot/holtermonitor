import matplotlib as mpl
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import bisect as bis
import bokeh.plotting as bp
import bokeh.models as bm
import bokeh.models.widgets as bmw
import bokeh.layouts as bl
import bokeh.io as bio
from bokeh.palettes import Reds8 as r8
from mpld3 import plugins, utils
import database_manager as dm
import holter_monitor_constants as hmc
import logging
log = logging.getLogger("hm_logger")


def render_full_plot(min=0,
                     max=2,
                     query_window=60):

    data_length = dm.query_length()
    pvcs = np.array(dm.query_pvcs())

    tools = "crosshair,save,xbox_zoom,xbox_select,xpan"

    fig = bp.figure(title="Holter Monitor Data Visualizer",
                    tools=tools,
                    x_axis_label="time (s)",
                    y_axis_label="ECG Signal (mV)",
                    y_range=(min, max))

    line_source = bm.ColumnDataSource(
        data=dict(
            time=[],
            ecg=[]
        )
    )

    fig.line('time', 'ecg', source=line_source)

    try:
        pvc_indices = pvcs[:, 0]
        pvc_certainties = pvcs[:, 1]
    except IndexError:
        pvc_indices = []
        pvc_certainties = []

    pvc_data = np.array(
        [list(t) for t in [dm.query_point(i) for i in pvc_indices]]
    )

    point_source = bm.ColumnDataSource(
        data=dict(
            time=pvc_data[:, 0],
            ecg=pvc_data[:, 1],
            certainty=pvc_certainties,
        )
    )

    r8.reverse()
    mapper = bm.LinearColorMapper(
        palette=r8,
        low=0,
        high=4
    )

    pvc_indicators = fig.circle(
        'time', 'ecg',
        source=point_source,
        size=15,
        fill_color={'field': 'certainty', 'transform': mapper},
        line_color=None,
        alpha=0.7
    )

    fig.add_tools(
        bm.HoverTool(
            renderers=[pvc_indicators],
            tooltips=[
                ("PVC detected at", "@{time}s"),
                ("Conditions met", "@{certainty}"),
            ]
        )
    )

    pvc_strings = format_pvcs(pvcs)

    window_slider = bmw.Slider(
        title="Window (seconds)",
        value=3,
        start=1,
        end=10,
        step=1
    )

    def update_range(left_time, right_time):
        fig.x_range.start = left_time
        fig.x_range.end = right_time

    if len(pvc_strings) > 0:
        pvc_select = bmw.Select(
            title="Detected " + str(len(pvcs)) + " PVCs:",
            value=pvc_strings[0],
            options=pvc_strings
        )

        def update_select():
            index = pvc_indices[pvc_strings.index(pvc_select.value)]
            w_range = hmc.SAMPLE_RATE * window_slider.value
            left, right = find_range(index, w_range, data_length)
            left_time = dm.query_point(left)[0]
            right_time = dm.query_point(right)[0]
            center = (left_time + right_time) / 2
            time, ecg = dm.query_data(center - query_window / 2, center + query_window / 2)
            line_source.data = dict(
                time=time,
                ecg=ecg
            )
            update_range(left_time, right_time)

        update_select()  # set initial display
        pvc_select.on_change("value", lambda attr, old, new: update_select())
    else:
        pvc_select = bmw.Div(
            text="""
            <b>No PVCs detected</b>
            """
        )

    def update_window():
        center = (fig.x_range.start + fig.x_range.end) / 2
        left_time = center - window_slider.value / 2
        right_time = center + window_slider.value / 2
        update_range(left_time, right_time)

    update_window()
    window_slider.on_change("value", lambda attr, old, new: update_window())

    title = "Holter Monitor Data Visualizer"
    # bp.output_file(html_filename, title=title, mode="inline")
    # bp.show(fig)

    inputs = bl.widgetbox(pvc_select)
    bio.curdoc().add_root(
        bl.row(
            bl.column(
                inputs,
                window_slider
            ),
            fig
        )
    )
    bio.curdoc().title = title
    log.debug("Successfully rendered full plot")


def format_pvcs(pvcs):
    """ formats pvcs into a list of readable strings

    :param pvcs: list of pvc indices and certainties from peak detection
    :return: list of pvc strings
    """
    return [
        str(round(pvc[1]))
        + " condition"
        + ("s" if round(pvc[1]) > 1 else "")
        + " met @ "
        + display_time(
            dm.query_point(pvc[0])[0]
        )
        for pvc in pvcs
    ]


def display_time(time):
    """ converts a time given in seconds to a readable formatted string

    :param time: time in seconds
    :return: time string
    """

    if time < 60:
        return str(int(round(time))) + "s"
    elif time < 3600:
        return str(int(time / 60)) + "m " + \
               str(int(round(time % 60))) + "s"
    else:
        return str(int(time / 3600)) + "h " + \
               str(int(round((time % 3600) / 60))) + "m"


class LinkedView(plugins.PluginBase):
    """ A plugin for linking the timeline to the EKG plot.

    """

    JAVASCRIPT = """
    mpld3.register_plugin("linkedview", LinkedViewPlugin);
    LinkedViewPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    LinkedViewPlugin.prototype.constructor = LinkedViewPlugin;
    LinkedViewPlugin.prototype.requiredProps = ["idpts",
                                                "idline",
                                                "data",
                                                "tooltips"];
    LinkedViewPlugin.prototype.defaultProps ={alpha_bg:0.3,
                                              alpha_fg:1.0,
                                              small_size:1,
                                              large_size:3}
    function LinkedViewPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    LinkedViewPlugin.prototype.draw = function(){
      var pts = mpld3.get_element(this.props.idpts);
      var line = mpld3.get_element(this.props.idline);
      var data = this.props.data;
      var tooltips = this.props.tooltips;
      alpha_fg = this.props.alpha_fg;
      alpha_bg = this.props.alpha_bg;
      small_size = this.props.small_size;
      large_size = this.props.large_size;
      var sel = null;

      var div = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("text-align", "center")
            .style("width", "180px")
            .style("height", "18px")
            .style("padding", "2px")
            .style("font", "12px sans-serif")
            .style("color", "white")
            .style("background", "#001A57")
            .style("border", "0px")
            .style("border-radius", "8px")
            .style("pointer-events", "none")
            .style("opacity", 0);

      if (data.length == 0) {
        this.fig.canvas.append("text")
            .text("No PVCs detected")
            .style("font-size", 40)
            .style("opacity", 0.3)
            .style("text-anchor", "middle")
            .attr("x", this.fig.width / 2)
            .attr("y", this.fig.height * 3 / 4)
      }

      function mouseover(d, i){
        line.data = data[i];
        line.elements().transition()
            .attr("d", line.datafunc(line.data))
            .style("stroke", this.style.fill);
        if (sel != null) {
          d3.select(sel).transition().duration(250)
                            .style("stroke-width", small_size)
                            .style("stroke-opacity", alpha_bg)
                            .style("fill-opacity", alpha_bg);
        }
        d3.select(this).transition().duration(250)
                            .style("stroke-width", large_size)
                            .style("stroke-opacity", alpha_fg)
                            .style("fill-opacity", alpha_fg);
        sel = this;

        div.transition()
                .duration(250)
                .style("opacity", .9);
        div.html(tooltips[i])
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 30) + "px");
      }

      function mousemove(d, i){
        div
        .style("left", (d3.event.pageX + 5) + "px")
        .style("top", (d3.event.pageY - 25) + "px");
      }

      function mouseout(d, i){
        div.transition()
            .duration(250)
            .style("opacity", 0);
      }

      pts.elements().on("mouseover", mouseover);
      pts.elements().on("mousemove", mousemove);
      pts.elements().on("mouseout", mouseout);
    };
    """

    def __init__(self, points, line, linedata, labels):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata,
                      "tooltips": labels,
                      "alpha_bg": 0.3,
                      "alpha_fg": 1.0,
                      "small_size": 1,
                      "large_size": 3}


def find_range(index, window, max):
    """ find the left and right endpoints of a window in an array

    :param index: index window is to be centered at
    :param window: the length of the window
    :param max: the size of the array
    :return: left and right endpoints of the window
    """
    half_window = int(window / 2)

    return (
        (index - half_window, index + half_window)  # in range
        if max - half_window >= index >= half_window else
        (max - window, max)  # too far on right
        if max - half_window < index else
        (0, window)  # to far on left
    )


def render_pvc_plot(time, ecg, pvcs, window=3, html_filename="pvcs.html"):
    """ renders an interactive plot in a browser for viewing PVCs over 24 hrs

    :param time: time data array corresponding to the ecg data array
    :param ecg: ecg data read in from an LVM or binary file
    :param pvcs: an array that stores the indices of the detected PVCs
    :param window: the number of seconds of EKG to display in the top window
    :param html_filename: the name of the html file where the output is saved
    :return:
    """

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
    ax[0].set_xlabel('Time (seconds)')
    ax[0].set_ylabel('ECG signal (mV)')

    try:
        pvc_indices = pvcs[:, 0]
        pvc_times = np.take(time, pvc_indices) / divisor
        pvc_strengths = pvcs[:, 1]
    except IndexError:
        # No PVCs detected
        pvc_indices = []
        pvc_times = []
        pvc_strengths = []
    ax[1].vlines(pvc_times, np.zeros(len(pvc_times)), pvc_strengths, alpha=0.3)
    points = ax[1].scatter(pvc_times,
                           pvc_strengths,
                           c=pvc_strengths,
                           s=250, alpha=0.3)

    # create the line and data objects
    x = np.take(time, range(0, window_range))
    waveform_data = \
        np.array(
            [[x,
              np.take(
                  ecg,
                  range(*find_range(index, window_range, len(ecg)))
              )]
             for index in pvc_indices])
    lines = ax[0].plot(x, 0 * x, '-w', lw=3, alpha=0.7)
    ax[0].set_ylim(0, 2)

    # transpose line data and add plugin
    try:
        linedata = waveform_data.transpose(0, 2, 1).tolist()
    except ValueError:
        # No PVCs detected
        linedata = []
        pass

    labels = ['PVC detected at {0}'.format(display_time(time))
              for time in pvc_times]

    plugins.connect(fig, LinkedView(points, lines[0], linedata, labels))

    mpld3.save_html(fig, html_filename)
    mpld3.show()
    log.debug("Successfully rendered PVC plot")
