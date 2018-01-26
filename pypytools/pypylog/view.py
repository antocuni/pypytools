import sys
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pypytools.pypylog import parse
from pypytools.pypylog import model

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
        #
        # XXX: if we call this method, the program segfaults when exiting; not
        # sure what is it about
        self.make_legend_handlers()

    def make_legend_handlers(self):
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

    @staticmethod
    def global_config():
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(useOpenGL=True)

    def make_charts(self):
        colors = [
            '4D4D4D',
            '5DA5DA',
            'FAA43A',
            '60BD68',
            'F17CB0',
            'B2912F',
            'B276B2',
            'DECF3F',
            'F15854',
        ]
        for i, (name, events) in enumerate(self.log.sections.iteritems()):
            if name == 'jit-backend-dump':
                continue
            color = colors[i % len(colors)]
            step_chart = model.make_step_chart(events)
            self.plot_item.plot(name=name,
                                x=step_chart.X, y=step_chart.Y,
                                connect='pairs',
                                pen=color)

    def show(self):
        self.app.exec_()

    def eventFilter(self, source, event):
        # press ESC to quit
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Escape, ord('Q')):
                self.app.quit()
        return False

def main():
    viewer = LogViewer(sys.argv[1])
    viewer.show()



if __name__ == '__main__':
    main()
