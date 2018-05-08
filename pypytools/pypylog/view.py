import sys
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pypytools.pypylog import parse
from pypytools.pypylog import model

#PALETTE = ['#8dd3c7','#ffffb3','#bebada','#fb8072','#80b1d3','#fdb462','#b3de69','#fccde5','#d9d9d9','#bc80bd','#ccebc5','#ffed6f']

PALETTE = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928']
COLORS = {
    'gc-set-nursery-size': None,
    'gc-hardware': None,
    'jit-summary': None,
    'jit-abort-log': None,
    'jit-disableinlining': None,
    'jit-abort': None,
    'jit-log-compiling-loop': None,
    'jit-log-short-preamble': None,
    'jit-log-opt-loop': None,
    'jit-mem-collect': None,
    'jit-abort-longest-function': None,
    'jit-log-compiling-bridge': None,
    'jit-log-noopt': None,

    'gc-minor': PALETTE[0],
    'gc-minor-walkroots': None, # PALETTE[1],
    'gc-collect-step': PALETTE[2],
    'gc-collect-done': PALETTE[1],

    'jit-log-opt-bridge': PALETTE[3],
    'jit-mem-looptoken-alloc': PALETTE[4],
    'jit-log-rewritten-bridge': PALETTE[5],
    'jit-backend-addr': PALETTE[6],
    'jit-trace-done': PALETTE[7],
    'jit-backend-dump': None, # PALETTE[8],
    'jit-optimize': PALETTE[9],
    'jit-backend': PALETTE[10],
    'jit-tracing': PALETTE[11],
}

class LogViewer(QtCore.QObject):

    def __init__(self, fname, chart_type='dot'):
        QtCore.QObject.__init__(self)
        self.global_config()
        self.log = parse.flat(fname, model.GroupedPyPyLog())
        self.chart_type = chart_type
        #self.log.print_summary()
        self.app = pg.mkQApp()
        # main window
        self.win = pg.GraphicsWindow(title=fname)
        self.win.installEventFilter(self) # capture key presses
        self.scene = self.win.scene()
        #
        # main plot item, inside the window
        self.plot_item = self.win.addPlot()
        self.legend = self.plot_item.addLegend()
        self.make_charts()
        self.add_legend_handlers()
        self.set_axes()

    @staticmethod
    def global_config():
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(useOpenGL=True)
        ## pg.setConfigOption('background', 0.95)
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
        x_axis = self.plot_item.axes['bottom']['item']
        y_axis = self.plot_item.axes['left']['item']
        x_axis.setGrid(50)
        y_axis.setGrid(50)

    def make_charts(self):
        sections = sorted(self.log.sections)
        for i, name in enumerate(sections):
            color = COLORS[name]
            if color is None:
                continue
            events = self.log.sections[name]
            self.make_one_chart(self.chart_type, name, color, events)

    def make_one_chart(self, t, name, color, events):
        if t == 'step':
            step_chart = model.make_step_chart(events)
            pen = pg.mkPen(color, width=3)
            self.plot_item.plot(name=name,
                                x=step_chart.X,
                                y=step_chart.Y,
                                connect='pairs',
                                pen=pen)
        elif t == 'dot':
            pen = pg.mkPen(color)
            brush = pg.mkBrush(color)
            s = model.Series.from_points([ev.as_point() for ev in events])
            self.plot_item.scatterPlot(name=name, x=s.X, y=s.Y, size=2,
                                       pen=pen, brush=brush)
        else:
            raise ValueError('Unknown char type: %s' % t)

    def add_legend_handlers(self):
        # toggle visibility of plot by clicking on the legend
        for sample, label in self.legend.items:
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
        for sample, label in self.legend.items:
            del sample.mouseClickEvent
            del label.mouseClickEvent

    def get_curve(self, name):
        for curve in self.plot_item.curves:
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


def main():
    viewer = LogViewer(sys.argv[1], 'dot')
    viewer.show()

if __name__ == '__main__':
    main()
