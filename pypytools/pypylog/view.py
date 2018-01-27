import sys
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pypytools.pypylog import parse
from pypytools.pypylog import model

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

    'gc-minor': '#f768a1',
    'gc-minor-walkroots': '#c51b8a',
    'gc-collect-step': '#7a0177',
 
    'jit-log-opt-bridge': '#ffffd9',
    'jit-mem-looptoken-alloc': '#edf8b1',
    'jit-log-rewritten-bridge': '#c7e9b4',
    'jit-backend-addr': '#7fcdbb',
    'jit-trace-done': '#41b6c4',
    'jit-backend-dump': None, # '#1d91c0',
    'jit-optimize': '#225ea8',
    'jit-backend': '#253494',
    'jit-tracing': '#081d58',
}

class LogViewer(QtCore.QObject):

    def __init__(self, fname):
        QtCore.QObject.__init__(self)
        self.global_config()
        self.log = parse.flat(fname, model.GroupedPyPyLog())

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
        pg.setConfigOption('background', 0.95)
        pg.setConfigOption('foreground', 'k')

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
        for i, (name, events) in enumerate(self.log.sections.iteritems()):
            color = COLORS[name]
            if color is None:
                continue
            step_chart = model.make_step_chart(events)
            self.plot_item.plot(name=name,
                                x=step_chart.X, y=step_chart.Y,
                                connect='pairs',
                                pen=color)

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
    viewer = LogViewer(sys.argv[1])
    viewer.show()



if __name__ == '__main__':
    main()
