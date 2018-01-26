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
        #
        # main plot item, inside the window
        self.plot_item = self.win.addPlot()
        self.legend = self.plot_item.addLegend()
        self.make_charts()

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
