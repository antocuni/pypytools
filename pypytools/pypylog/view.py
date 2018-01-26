import sys
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pypytools.pypylog import parse
from pypytools.pypylog import model

class LogViewer(object):

    def __init__(self, fname):
        self.global_config()
        self.log = parse.flat(fname, model.GroupedPyPyLog())
        self.app = pg.mkQApp()
        self.win = pg.plot(title=fname)
        self.win.addLegend()
        self.plot()

    @staticmethod
    def global_config():
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(useOpenGL=True)

    def plot(self):
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
            self.win.plot(name=name,
                          x=step_chart.X, y=step_chart.Y,
                          connect='pairs',
                          pen=color)

    def show(self):
        self.app.exec_()


def main():
    viewer = LogViewer(sys.argv[1])
    viewer.show()



if __name__ == '__main__':
    main()
