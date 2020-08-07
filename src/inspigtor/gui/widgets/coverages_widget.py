"""This module implements the class CoveragesWidget.
"""

from PyQt5 import QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.helper_functions import func_formatter
from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton
from inspigtor.kernel.utils.helper_functions import build_timeline


class CoveragesWidget(QtWidgets.QWidget):
    """This class implements the widgets that stores the coverage plot.

    A coverage plot is a plot which indicates for each record interval the ratio of float-evaluable values over the total number of values.
    A ratio of 1 indicates that all values could be successfully casted to a float.
    """

    def __init__(self, parent=None):

        super(CoveragesWidget, self).__init__(parent)

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

        if not coverages:
            return

        n_intervals = len(coverages)

        x = range(0, n_intervals)
        interval_data = self.parent().interval_settings_label.data()

        tick_labels = range(1, n_intervals+1) if interval_data is None else build_timeline(-10, int(interval_data[2]), x)

        self._axes.clear()
        self._axes.plot(x, coverages)
        self._axes.set_xlabel('interval')
        self._axes.xaxis.set_minor_locator(ticker.AutoLocator())
        self._axes.xaxis.set_minor_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))
        self._axes.xaxis.set_major_locator(ticker.IndexLocator(base=10.0, offset=0.0))
        self._axes.xaxis.set_major_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))
        self._axes.set_ylabel('coverage')

        self._canvas.draw()
