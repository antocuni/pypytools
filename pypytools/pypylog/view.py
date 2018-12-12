"""
Usage: view FILE [options]

Options:
  --dot             Plot the events as dots [default: True]
  --step            Plot the events as steps
  --tsc-freq=FREQ   Convert the TSC counter to seconds with the specified
                    frequency [default: auto]
"""

import sys
from collections import defaultdict
import docopt
import cpuinfo
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pypytools.pypylog import parse
from pypytools.pypylog import model

def make_palette(n):
    """
    Manually run this function if you want to tweak the color
    palette. Normally, the palette is hard-coded, to avoid a dependency on
    matplotlib and seaborn
    """
    from matplotlib.colors import to_hex
    import seaborn as sns
    #palette = sns.hls_palette(n)
    palette = sns.color_palette("Set1", n)
    #palette = sns.color_palette("Dark2", n)
    hex_palette = [str(to_hex(c)) for c in palette]
    print 'PALETTE = %r # %d colors' % (hex_palette, n)
    return hex_palette
    ## import matplotlib
    ## sns.palplot(PALETTE)
    ## matplotlib.pyplot.show()

PALETTE = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628'] # 7 colors
#PALETTE = make_palette(7)

COLORS = {
    'gc-minor': PALETTE[0],
    'gc-collect-step': PALETTE[1],
    'gc-minor memory': PALETTE[2],

    'jit-optimize': PALETTE[3],
    'jit-backend': PALETTE[4],
    'jit-tracing': PALETTE[5],
    'jit-mem-collect': PALETTE[6],

    # uninteresting sections
    'gc-collect-done': None,
    'gc-hardware': None,
    'gc-minor-walkroots': None,
    'gc-set-nursery-size': None,
    'jit-abort': None,
    'jit-abort-log': None,
    'jit-abort-longest-function': None,
    'jit-backend-addr': None,
    'jit-backend-counts': None,
    'jit-backend-dump': None,
    'jit-disableinlining': None,
    'jit-log-compiling-bridge': None,
    'jit-log-compiling-loop': None,
    'jit-log-exported-state': None,
    'jit-log-noopt': None,
    'jit-log-opt-bridge': None,
    'jit-log-opt-loop': None,
    'jit-log-rewritten-bridge': None,
    'jit-log-rewritten-loop': None,
    'jit-log-short-preamble': None,
    'jit-mem-looptoken-alloc': None,
    'jit-summary': None,
    'jit-trace-done': None,
}

COLORS.update({
    'SCANNING': '#00FF00',
    'MARKING': '#FFFFFF',
    'SWEEPING': '#FFFF00',
    'FINALIZING': '#FF00FF',
    })


class LogViewer(QtCore.QObject):

    def __init__(self, fname, chart_type, freq):
        QtCore.QObject.__init__(self)
        self.global_config()
        self.log = parse.gc(fname, model.GroupedPyPyLog(), freq)
        self.chart_type = chart_type
        self.log.print_summary()
        self.app = pg.mkQApp()
        # main window
        self.win = pg.GraphicsWindow(title=fname)
        self.win.installEventFilter(self) # capture key presses
        self.scene = self.win.scene()
        #
        # plot items, inside the window: we have a different plot item for
        # each Y axis (e.g., one for plotting time and another for potting
        # memory).
        #
        # we create plot_time for last: it's the one which is controlled by
        # dragging the mouse
        self.mem_plot = self.win.addPlot(0, 0)
        self.time_plot = self.win.addPlot(0, 0)
        #
        self.time_plot.setLabel('left', 'Time', 's')
        self.time_plot.setLabel('bottom', 'Time', 's')
        self.time_plot.getAxis('bottom').enableAutoSIPrefix(False)
        #
        self.mem_plot.setXLink(self.time_plot)
        self.mem_plot.showAxis('left', False)
        self.mem_plot.showAxis('bottom', False)
        self.mem_plot.showAxis('right')
        self.mem_plot.setLabel('right', 'Memory', 'B')
        #
        self.time_legend = self.time_plot.addLegend()
        self.mem_legend = self.mem_plot.addLegend(offset=(-30, 30))
        self.make_charts()
        self.add_legend_handlers()
        self.set_axes()

    @staticmethod
    def global_config():
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(useOpenGL=True)
        pg.setConfigOption('background', 0.1)
        ## pg.setConfigOption('foreground', 'k')

    def __del__(self):
        self.remove_legend_handlers()

    def show(self):
        self.app.exec_()

    def eventFilter(self, source, event):
        # press ESC to quit
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Escape, ord('Q')):
                self.app.quit()
        return False

    def set_axes(self):
        x_axis = self.time_plot.axes['bottom']['item']
        y_axis = self.time_plot.axes['left']['item']
        x_axis.setGrid(50)
        y_axis.setGrid(50)

    def make_charts(self):
        sections = sorted(self.log.sections)
        for i, name in enumerate(sections):
            if name not in COLORS:
                print 'WARNING: unexpected section %s, ignoring' % name
                COLORS[name] = None
            color = COLORS[name]
            if color is None:
                continue
            events = self.log.sections[name]
            self.make_one_chart(self.chart_type, name, color, events)
        #
        self.make_gc_minor_mem()

    def make_gc_minor_mem(self):
        name = 'gc-minor memory'
        color = COLORS[name]
        events = self.log.sections['gc-minor']
        s = model.Series(len(events))
        for i, ev in enumerate(events):
            s[i] = ev.start, ev.memory
        #print 'Max memory:', s.Y.max()
        self.mem_plot.plot(name=name, x=s.X, y=s.Y, pen=pg.mkPen(color))

    def make_gc_collect_step(self, name, color):
        # draw a plot of gc-collect-step, making sure that each major
        # collection is disconnected from the other ones. We consider a major
        # collection done when we see a transition from FINALIZING to
        # SCANNING.
        pen = pg.mkPen(color)
        steps = self.log.sections['gc-collect-step']
        NaN = float('NaN')
        points = []
        last_ev = None
        phases = defaultdict(list)
        for ev in steps:
            if (last_ev and last_ev.phase == 'FINALIZING' and
                ev.phase == 'SCANNING'):
                points.append((last_ev.start, NaN))
                points.append((ev.start, NaN))
            points.append(ev.as_point())
            last_ev = ev
            phases[ev.phase].append(ev)
        s = model.Series.from_points(points)
        self.time_plot.plot(name=name, x=s.X, y=s.Y, pen=pen, connect='finite')
        #
        # draw points of different colors for each distinct phase
        size = 3
        for phase in ('SCANNING', 'MARKING', 'SWEEPING', 'FINALIZING'):
            color = COLORS[phase]
            self.make_scatter_plot(phase, color, size, phases[phase])

    def make_one_chart(self, t, name, color, events):
        if name == 'gc-collect-step':
            self.make_gc_collect_step(name, color)
        elif t == 'step':
            step_chart = model.make_step_chart(events)
            pen = pg.mkPen(color, width=3)
            self.time_plot.plot(name=name,
                                x=step_chart.X,
                                y=step_chart.Y,
                                connect='pairs',
                                pen=pen)
        elif t == 'dot':
            size = 2
            self.make_scatter_plot(name, color, size, events)
        else:
            raise ValueError('Unknown char type: %s' % t)

    def make_scatter_plot(self, name, color, size, events):
        pen = pg.mkPen(color)
        brush = pg.mkBrush(color)
        size = 2
        s = model.Series.from_events(events)
        item = self.time_plot.scatterPlot(name=name, x=s.X, y=s.Y, size=size,
                                          pen=pen, brush=brush)
        for ev, p in zip(events, item.scatter.points()):
            p.event = ev
        item.sigPointsClicked.connect(self.on_points_clicked)

    def on_points_clicked(self, item, points):
        for p in points:
            print getattr(p, 'event', None)

    def add_legend_handlers(self):
        # toggle visibility of plot by clicking on the legend
        items = (self.time_legend.items +
                 self.mem_legend.items)
        for sample, label in items:
            def clicked(ev, sample=sample, label=label):
                name = label.text
                curve = self.get_curve(name)
                if curve is None:
                    print 'Cannot find curve', name
                    return
                self.set_curve_visibility(curve, sample, label,
                                          not curve.isVisible())
            #
            sample.mouseClickEvent = clicked
            label.mouseClickEvent = clicked

    def remove_legend_handlers(self):
        # delete the mouseClickEvent attributes which were added by
        # add_legend_handlers: if we don't, we get a segfault during shutdown
        # (not sure why)
        items = (self.time_legend.items +
                 self.mem_legend.items)
        for sample, label in items:
            del sample.mouseClickEvent
            del label.mouseClickEvent

    def get_curve(self, name):
        curves = (self.time_plot.curves +
                  self.mem_plot.curves)
        for curve in curves:
            if curve.name() == name:
                return curve
        return None

    def set_curve_visibility(self, curve, sample, label, visible):
        if visible:
            sample.setOpacity(1)
            label.setOpacity(1)
            curve.show()
        else:
            sample.setOpacity(0.5)
            label.setOpacity(0.5)
            curve.hide()

def get_frequency(freq):
    if freq == 'auto':
        freq = cpuinfo.get_cpu_info()['hz_advertised_raw'][0] # Hz
        return float(freq)
    else:
        return parse.parse_frequency(freq)

def main(argv=None):
    args = docopt.docopt(__doc__, argv=argv)
    chart_type = 'dot'
    if args['--step']:
        chart_type = 'step'
    freq = get_frequency(args['--tsc-freq'])
    viewer = LogViewer(args['FILE'], chart_type, freq)
    viewer.show()

if __name__ == '__main__':
    main()
