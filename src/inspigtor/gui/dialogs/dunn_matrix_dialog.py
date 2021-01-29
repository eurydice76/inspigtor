import numpy as np

from PyQt5 import QtCore, QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class DunnMatrixDialog(QtWidgets.QDialog):
    """This class implements a dialog that will show the averages of a given property for the different pigs.
    """

    def __init__(self, dunn_matrix, parent):

        super(DunnMatrixDialog, self).__init__(parent)

        self._dunn_matrix = dunn_matrix

        self.init_ui()

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._canvas)
        main_layout.addWidget(self._toolbar)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self.setWindowTitle('Dunn matrix')

        # Build the matplotlib imshoxw widget
        self._figure = Figure()
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        self._axes.clear()
        plot = self._axes.imshow(self._dunn_matrix, aspect='equal', origin='lower', interpolation='nearest')
        self._axes.set_xticks(range(0, self._dunn_matrix.shape[0]))
        self._axes.set_yticks(range(0, self._dunn_matrix.shape[1]))
        self._axes.set_xticklabels(self._dunn_matrix.index)
        self._axes.set_yticklabels(self._dunn_matrix.index)
        loc = ticker.MaxNLocator(10)
        self._axes.xaxis.set_major_locator(loc)
        for tick in self._axes.xaxis.get_major_ticks():
            tick.label.set_fontsize(8)
            tick.label.set_rotation('vertical')

        self._axes.yaxis.set_major_locator(loc)
        for tick in self._axes.yaxis.get_major_ticks():
            tick.label.set_fontsize(8)

        self._figure.colorbar(plot)

        self._canvas.draw()

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()
