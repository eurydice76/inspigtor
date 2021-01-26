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
        self._axes.set_ylabel('coverage')
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbarWithExportButton(self._canvas, self)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

    def update_coverage_plot(self, reader, selected_property):
        """Update the coverage plot

        Args:
            reader (): the reader for which the coverage plot should be set
            selected_property: the selected property
        """

        coverages = reader.get_coverages(selected_property)

        if not coverages:
            return

        self._axes.clear()

        timeline = reader.timeline

        self._axes.plot(timeline, coverages)
        loc = ticker.IndexLocator(base=10.0, offset=reader.t_initial_interval_index)
        self._axes.xaxis.set_major_locator(loc)
        for tick in self._axes.xaxis.get_major_ticks():
            tick.label.set_fontsize(6)

        self._axes.set_ylabel('coverage')

        self._canvas.draw()
