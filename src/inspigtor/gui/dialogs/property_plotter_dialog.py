import numpy as np

from PyQt5 import QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class PropertyPlotterDialog(QtWidgets.QDialog):

    def __init__(self, main_window):

        super(PropertyPlotterDialog, self).__init__(main_window)

        self._main_window = main_window

        self.init_ui()

    def build_layout(self):

        self._main_layout = QtWidgets.QVBoxLayout()

        self._main_layout.addWidget(self._canvas)
        self._main_layout.addWidget(self._toolbar)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(self._main_layout)

    def build_widgets(self):

        # Build the matplotlib imshow widget
        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

    def init_ui(self):
        """
        """

        self.build_widgets()

        self.build_layout()

    def plot_property(self, selected_property, xs, ys):

        self.setWindowTitle('Plot {}'.format(selected_property))

        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('index')
        self._axes.set_ylabel(selected_property)

        self._plot = self._axes.plot(xs, ys, 'ro')

        self._canvas.draw()
