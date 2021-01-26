import logging

import numpy as np

from PyQt5 import QtCore, QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.helper_functions import find_main_window, func_formatter
from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton
from inspigtor.kernel.readers.picco2_reader import PiCCO2FileReaderError
from inspigtor.kernel.utils.helper_functions import build_timeline


class IndividualAveragesDialog(QtWidgets.QDialog):
    """This class implements a dialog that will show the averages of a given property for the different pigs.
    """

    def __init__(self, pigs_model, parent):

        super(IndividualAveragesDialog, self).__init__(parent)

        self._pigs_model = pigs_model

        self._selected_property = self._pigs_model.selected_property

        self.init_ui()

    def build_events(self):
        """Set the signal/slots of the main window
        """

        self._selected_pig_combo.currentIndexChanged.connect(self.on_select_pig)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._canvas)
        main_layout.addWidget(self._toolbar)

        main_layout.addWidget(self._selected_pig_combo)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self.setWindowTitle('Individual averages for {} property'.format(self._selected_property))

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbarWithExportButton(self._canvas, self)

        pig_names = []
        for row in range(self._pigs_model.rowCount()):
            index = self._pigs_model.index(row)
            pig_names.append(self._pigs_model.data(index, QtCore.Qt.DisplayRole))

        self._selected_pig_combo = QtWidgets.QComboBox()
        self._selected_pig_combo.addItems(pig_names)

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

        self.on_select_pig(0)

    def on_select_pig(self, row):
        """Plot the averages and standard deviations over record intervals for a selected pig.

        Args:
            row (int): the selected pig
        """

        # Fetch the statistics (average and standard deviation) for the selected pig
        index = self._pigs_model.index(row)
        reader = self._pigs_model.data(index, self._pigs_model.Reader)
        try:
            individual_averages = reader.get_descriptive_statistics(self._selected_property, selected_statistics=['mean', 'std'])
        except PiCCO2FileReaderError as error:
            logging.error(str(error))
            return

        averages = []
        stds = []
        for interval, average, std in zip(individual_averages['intervals'], individual_averages['mean'], individual_averages['std']):
            averages.append(average)
            stds.append(std)

        # If there is already a plot, remove it
        if hasattr(self, '_axes'):
            self._axes.remove()

        # Plot the averages and standard deviations
        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel(self._selected_property)

        timeline = reader.timeline

        self._plot = self._axes.errorbar(timeline, averages, yerr=stds, fmt='ro')
        loc = ticker.IndexLocator(base=10.0, offset=reader.t_initial_interval_index)
        self._axes.xaxis.set_major_locator(loc)
        for tick in self._axes.xaxis.get_major_ticks():
            tick.label.set_fontsize(8)
            tick.label.set_rotation('vertical')

        self._canvas.draw()
