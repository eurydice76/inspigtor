import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton


class CoveragesWidget(QtWidgets.QWidget):
    """Ths class implements the widgets that stores the coverage plot.
    """

    def __init__(self, pigs_model, parent=None):

        super(CoveragesWidget, self).__init__(parent)

        self._pigs_model = pigs_model

        self.init_ui()

    def build_layout(self):
        """Build the layout.
        """

        self._main_layout = QtWidgets.QVBoxLayout()

        self._main_layout.addWidget(self._canvas)
        self._main_layout.addWidget(self._toolbar)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(self._main_layout)

    def build_widgets(self):
        """Builds the widgets.
        """

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel('coverage')
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbarWithExportButton(self._canvas, self)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

    def update_coverage_plot(self, coverages):
        """Update the coverage plot

        Args:
            coverages (list): the coverages values to plot
        """

        self._axes.clear()

        self._axes.plot(range(1, len(coverages)+1), coverages)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel('coverage')

        self._canvas.draw()
